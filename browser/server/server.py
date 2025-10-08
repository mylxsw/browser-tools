import dataclasses
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime

import requests
import tempfile
import pypdfium2 as pdfium
from pyzerox import zerox
from playwright.async_api import async_playwright

from browser.util.error import BusinessError


@dataclasses.dataclass
class MarkdownResult:
    markdown: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_tokens: int
    model: str


class BrowserServer:
    """
    BrowserServer class is responsible for converting HTML, URL, and PDF to images.
    """

    def __init__(
        self,
        temp_path: str,
        zerox_model: str = "gpt-4o-mini",
        browser_size: tuple[int, int] = (1080, 1920),
        page_timeout: int = 60000,
    ):
        self._temp_path = temp_path
        self._zerox_model = zerox_model
        self._browser_size = browser_size
        self._page_timeout = page_timeout

        # check if playwright browsers are installed
        try:
            print("Installing Playwright browsers...")
            subprocess.run([sys.executable, "-m", "playwright", "install", "--with-deps"], check=True)
            print("Playwright browsers installed successfully.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                "Could not install Playwright browsers. Please run 'playwright install --with-deps' manually."
            )

    def clean_before(self, before_date: datetime):
        """
        Clean up the temporary directory before a given date
        :param before_date: datetime before which to clean up
        """
        logging.info(f"cleaning up temporary files before {before_date}")
        for file in os.listdir(self._temp_path):
            file_to_delete = os.path.join(self._temp_path, file)
            if os.path.getmtime(file_to_delete) < before_date.timestamp():
                logging.info(f"cleaning up temporary file: remove {file_to_delete}")
                os.remove(file_to_delete)

    async def html_to_image(
        self,
        html_or_url: str,
        size: tuple[int, int] | None = None,
    ) -> list[str]:
        """
        Convert HTML or URL to image
        :param html_or_url: HTML string or URL
        :param size: Size of the browser window
        :return: list of image paths
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Set page timeout
            page.set_default_timeout(self._page_timeout)

            if size is None:
                size = self._browser_size
            await page.set_viewport_size({"width": size[0], "height": size[1]})

            if html_or_url.startswith(("http://", "https://")):
                await page.goto(html_or_url, wait_until="networkidle")
            else:
                await page.set_content(html_or_url, wait_until="networkidle")

            filename = self._generate_filename(html_or_url, "png", absolute=True)
            await page.screenshot(path=filename, full_page=True)

            await browser.close()

            return [filename]

    def generate_random_filename(self, ext: str) -> str:
        """
        Generate a random filename
        :param ext: Extension of the file
        :return: Random filename
        """
        return self._generate_filename(
            original_path=str(uuid.uuid4()), ext=ext, absolute=True
        )

    def _generate_filename(
        self,
        original_path: str,
        ext: str,
        index: int = 0,
        absolute: bool = False,
    ) -> str:
        """
        Build local path for the resource
        :param original_path: Original path
        :param index: Index of the resource
        :param ext: Extension of the resource
        :param absolute: Whether to return absolute path or not
        :return: Local path
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{today}-{uuid.uuid5(uuid.NAMESPACE_URL, original_path).hex}-{index}-{uuid.uuid4().hex}.{ext}"
        return f"{self._temp_path}/{filename}" if absolute else filename

    def _ensure_file_in_local(self, url: str, ext: str) -> str:
        """
        Download remote resource if necessary
        :param url: URL of the resource
        :param ext: Extension of the resource
        :return: Local path of the resource
        """
        if url.startswith(("http://", "https://")):
            response = requests.get(url)
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{ext}"
            ) as temp_file:
                temp_file.write(response.content)
                return temp_file.name
        else:
            return url

    def pdf_to_image(self, pdf_path: str) -> list[str]:
        """
        Convert PDF to images
        :param pdf_path: URL or local path of the PDF
        :return: list of image paths
        """
        local_path = self._ensure_file_in_local(pdf_path, "pdf")
        pdf = pdfium.PdfDocument(local_path)

        save_paths = []
        try:
            for page_num in range(len(pdf)):
                page = pdf.get_page(page_num)
                bitmap = page.render(scale=2)
                pil_img = bitmap.to_pil()

                save_path = self._generate_filename(
                    original_path=pdf_path, ext="png", index=page_num, absolute=True
                )
                pil_img.save(fp=save_path, format="png", optimize=True)
                save_paths.append(save_path)

                [g.close() for g in (pil_img, bitmap, page)]
        except Exception as e:
            logging.warning(f"Error in pdf_to_image: {e}")
        finally:
            pdf.close()

        return save_paths

    def pdf_to_text(self, pdf_path: str) -> str:
        """
        Convert PDF to text
        :param pdf_path: URL or local path of the PDF
        :return: text
        """
        text = ""

        pdf = pdfium.PdfDocument(self._ensure_file_in_local(pdf_path, "pdf"))
        try:
            for page_num in range(len(pdf)):
                page = pdf.get_page(page_num)
                text_page = page.get_textpage()
                text += text_page.get_text_bounded()
                [g.close() for g in (text_page, page)]
        except Exception as e:
            logging.error(f"Error in pdf_to_text: {e}")
        finally:
            pdf.close()

        return text

    async def pdf_to_markdown(
        self,
        pdf_path: str,
        maintain_format: bool = False,
    ) -> MarkdownResult:
        result = await zerox(
            file_path=pdf_path,
            model=self._zerox_model,
            cleanup=True,
            maintain_format=maintain_format,
        )
        return MarkdownResult(
            markdown="\n\n\n".join(page.content for page in result.pages),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cached_tokens=0,
            total_tokens=result.input_tokens + result.output_tokens,
            model=self._zerox_model,
        )