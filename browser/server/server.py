import dataclasses
import logging
import os
import uuid
from datetime import datetime

import requests
import tempfile
from html2image import Html2Image
import pypdfium2 as pdfium
from pyzerox import zerox

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
        browser_size: tuple[int, int] = (1024, 1024),
    ):
        self._temp_path = temp_path
        self._zerox_model = zerox_model
        self._html = Html2Image(
            size=browser_size,
            output_path=temp_path,
            disable_logging=True,
            temp_path=temp_path,
            custom_flags=["--timeout=10000"],
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

    def html_to_image(self, html_or_url: str) -> list[str]:
        """
        Convert HTML or URL to image
        :param html_or_url: HTML string or URL
        :return: list of image paths
        """
        try:
            filename = self._generate_filename(html_or_url, "png", absolute=False)

            if html_or_url.startswith(("http://", "https://")):
                return self._html.screenshot(url=html_or_url, save_as=filename)
            else:
                return self._html.screenshot(
                    html_str=html_or_url,
                    save_as=filename,
                    css_str="body { background: white; }",
                )
        except Exception as e:
            logging.warning(f"Error in html_to_image: {e}")
            raise BusinessError("Failed to convert HTML to image")

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
        self, original_path: str, ext: str, index: int = 0, absolute: bool = False
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
        self, pdf_path: str, maintain_format: bool = False
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
