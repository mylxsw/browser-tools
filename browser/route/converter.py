import base64
import logging
import os
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, UploadFile, Form

from browser.schema import (
    ImageResponse,
    TextResponse,
    TextWithTokenUsageResponse,
    TokenUsage,
)
from browser.server.server import BrowserServer
from browser.util.error import BusinessError


def route(server: BrowserServer) -> APIRouter:
    router = APIRouter(prefix="/browser")

    @contextmanager
    def file_to_local(file: UploadFile, ext: str):
        """
        Upload a file to local and call the callback function
        """
        local_path = server.generate_random_filename(ext=ext)
        try:
            with open(local_path, "wb") as f:
                f.write(file.file.read())

            yield local_path
        finally:
            try:
                if os.path.exists(local_path):
                    os.remove(local_path)
            except Exception as e:
                logging.error(f"Error in removing file: {e}")

    @router.post(
        "/pdf/to-image",
        summary="Convert a PDF file to an image",
        responses={200: {"model": ImageResponse}},
    )
    def pdf_to_image(
        source_file: Annotated[UploadFile, Form(description="The pdf file")],
    ):
        """
        Convert a PDF file to an image
        """

        with file_to_local(source_file, "pdf") as local_pdf_path:
            try:
                image_paths = server.pdf_to_image(pdf_path=local_pdf_path)
            except Exception as e:
                image_paths = []
                logging.warning(f"Error in converting PDF to image: {e}")

            if len(image_paths) == 0:
                raise BusinessError("No image generated")

            try:
                with open(image_paths[0], "rb") as f:
                    return ImageResponse(
                        image_base64=base64.b64encode(f.read()).decode("utf-8"),
                        image_type="png",
                    )
            finally:
                for image_path in image_paths:
                    if os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            logging.error(f"Error in removing file: {e}")

    @router.post(
        "/pdf/to-text",
        summary="Convert a PDF file to an text",
        responses={200: {"model": TextResponse}},
    )
    def pdf_to_text(
        source_file: Annotated[UploadFile, Form(description="The pdf file")],
    ):
        with file_to_local(source_file, "pdf") as local_pdf_path:
            text = server.pdf_to_text(pdf_path=local_pdf_path)
            return TextResponse(text=text)

    @router.post(
        "/pdf/to-markdown",
        summary="Convert a PDF file to an markdown",
        responses={200: {"model": TextWithTokenUsageResponse}},
    )
    async def pdf_to_markdown(
        source_file: Annotated[UploadFile, Form(description="The pdf file")],
        maintain_format: Annotated[
            bool | None,
            Form(description="Whether to maintain the format", alias="maintainFormat"),
        ] = False,
    ):
        with file_to_local(source_file, "pdf") as local_pdf_path:
            resp = await server.pdf_to_markdown(
                pdf_path=local_pdf_path, maintain_format=maintain_format or False
            )
            return TextWithTokenUsageResponse(
                text=resp.markdown,
                token_usage=TokenUsage(
                    total_tokens=resp.total_tokens,
                    input_tokens=resp.input_tokens,
                    output_tokens=resp.output_tokens,
                    cached_tokens=resp.cached_tokens,
                    model=resp.model,
                ),
            )

    @router.post(
        "/html/to-image",
        summary="Convert a HTML to an image",
        responses={200: {"model": ImageResponse}},
    )
    async def html_to_image(
        html_or_url: Annotated[str, Form(description="The HTML content or URL")],
        size: Annotated[
            str | None,
            Form(
                description="The size of the browser window, format: WIDTHxHEIGHT, e.g. 1080x1920",
                regex=r"^\d+x\d+$",
            ),
        ] = "1080x1920",
    ):
        image_size = None
        if size:
            try:
                width, height = map(int, size.split("x"))
                image_size = (width, height)
            except ValueError:
                raise BusinessError("Invalid size format. Expected WIDTHxHEIGHT.")

        images = await server.html_to_image(
            html_or_url=html_or_url, size=image_size
        )
        if len(images) == 0:
            raise BusinessError("No image generated")

        try:
            with open(images[0], "rb") as f:
                return ImageResponse(
                    image_base64=base64.b64encode(f.read()).decode("utf-8"),
                    image_type="png",
                )
        finally:
            for image_path in images:
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        logging.error(f"Error in removing file: {e}")

    return router
