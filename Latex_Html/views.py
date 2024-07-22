import subprocess
import re
import logging
import os
from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework import status
import tempfile
import html


logger = logging.getLogger(__name__)

class ConvertirLatex(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        latex_code = request.data.get('latex_code', '').strip()

        if not latex_code or len(latex_code) < 10:
            logger.error("Invalid or insufficient LaTeX code provided")
            return Response({"error": "Invalid or insufficient LaTeX code provided"}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"latex_conversion_{hash(latex_code)}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached result")
            return Response({"html_code": cached_result}, status=status.HTTP_200_OK)

        html_code = self.convert_latex_to_html(latex_code, request)
        if isinstance(html_code, Response):
            return html_code

        cache.set(cache_key, html_code, timeout=settings.CACHE_TIMEOUT)
        logger.info("Conversion result cached")
        return Response({"html_code": html_code}, status=status.HTTP_200_OK)

    def convert_latex_to_html(self, latex_code, request):
        try:
            tikz_blocks = re.findall(r'\\begin\{tikzpicture\}(.*?)\\end\{tikzpicture\}', latex_code, re.DOTALL)
            placeholder_map = {}

            for i, tikz_code in enumerate(tikz_blocks):
                placeholder = f"<img-placeholder-{i}>"
                latex_code = latex_code.replace(f"\\begin{{tikzpicture}}{tikz_code}\\end{{tikzpicture}}", placeholder)
                placeholder_map[placeholder] = tikz_code

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tex', encoding='utf-8') as tex_file:
                tex_file.write(latex_code)
                tex_filename = tex_file.name

            pandoc_command = ['pandoc', '--from=latex', '--to=html', '--mathjax', '--standalone', tex_filename]
            process = subprocess.run(pandoc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')

            if process.returncode != 0:
                logger.error(f"Pandoc conversion failed with error: {process.stderr}")
                return Response({"error": "Pandoc conversion failed", "details": process.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            html_code = html.unescape(process.stdout)

            for placeholder, tikz_code in placeholder_map.items():
                svg_path = self.generate_svg_from_tikz(tikz_code)
                if svg_path:
                    svg_url = f"{request.build_absolute_uri('/')[:-1]}{settings.STATIC_URL}{svg_path}"
                    img_element = f"<img src='{svg_url}' alt='Aquí debería agregar las imagenes Tikz Transformadas a SVG'>"
                    html_code = html_code.replace(placeholder, img_element)

            html_code = html_code.replace('<p><img', '<img')
            html_code = html_code.replace('></p>', '>')

            return html_code

        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            return Response({"error": "Conversion failed", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if os.path.exists(tex_filename):
                os.remove(tex_filename)

    def generate_svg_from_tikz(self, tikz_code, index=None):
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'tikz_conversions')
        os.makedirs(static_dir, exist_ok=True)

        try:
            if index is None:
                index = 0
            tex_file_path = os.path.join(static_dir, f'tikz_temp_{index}.tex')
            dvi_file_path = tex_file_path.replace('.tex', '.dvi')
            svg_file_path = tex_file_path.replace('.tex', '.svg')

            with open(tex_file_path, 'w', encoding='utf-8') as file:
                file.write(r"\documentclass{standalone}\usepackage{pgfplots}\pgfplotsset{compat=1.18}\begin{document}\begin{tikzpicture}")
                file.write(tikz_code)
                file.write(r"\end{tikzpicture}\end{document}")

            latex_command = ['latex', '-interaction=nonstopmode', '-output-directory', static_dir, tex_file_path]
            subprocess.run(latex_command, check=True)

            dvisvgm_command = ['dvisvgm', '--no-fonts', '-o', svg_file_path, dvi_file_path]
            subprocess.run(dvisvgm_command, check=True)

            relative_svg_path = os.path.join('tikz_conversions', f'tikz_temp_{index}.svg')
            return relative_svg_path

        except Exception as e:
            print(f"Failed to convert TikZ to SVG: {str(e)}")
            return None