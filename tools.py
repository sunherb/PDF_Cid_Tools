import re
import logging
from PyPDF2 import PdfReader


class PdfCidToUnicodeMapper:
    def __init__(self, pdf_path, target_font, logger=None):
        self.pdf_path = pdf_path
        self.target_font = target_font
        self.cid_to_unicode = {}
        self.cid_to_unicode_pattern = re.compile(r"<([0-9A-Fa-f]+)> <([0-9A-Fa-f]+)>")
        
        # 设置日志记录器
        self.logger = logger or self._setup_logger()

    def _setup_logger(self):
        """
        设置默认的日志记录器
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def extract_mapping(self):
        """
        从 PDF 中提取 CID 到 Unicode 的映射关系
        """
        try:
            reader = PdfReader(self.pdf_path)
            self.logger.info(f"Starting to extract CID to Unicode mapping from {self.pdf_path}.")

            # 遍历每个页面
            for page_number, page in enumerate(reader.pages, start=1):
                if "/Font" in page["/Resources"]:
                    fonts = page["/Resources"]["/Font"]
                    if self.target_font in fonts:
                        font_obj = fonts[self.target_font].get_object()
                        # 检查字体是否包含 ToUnicode 映射
                        if "/ToUnicode" in font_obj:
                            to_unicode_stream = font_obj["/ToUnicode"].get_data().decode("utf-8", errors="ignore")
                            self._parse_to_unicode_stream(to_unicode_stream)
                    else:
                        self.logger.warning(f"Target font {self.target_font} not found on page {page_number}.")
        except Exception as e:
            self.logger.error(f"Error occurred while processing the PDF: {e}")

    def _parse_to_unicode_stream(self, to_unicode_stream):
        """
        解析 ToUnicode 字符串流，提取 CID 到 Unicode 的映射
        """
        for match in self.cid_to_unicode_pattern.finditer(to_unicode_stream):
            cid = int(match.group(1), 16)
            unicode_char = chr(int(match.group(2), 16))
            self.cid_to_unicode[cid] = unicode_char
        self.logger.debug(f"Parsed {len(self.cid_to_unicode)} CID to Unicode mappings.")

    def get_char_from_cid(self, cid_x):
        """
        根据 CID 查找对应的字符
        """
        try:
            cid_num = int(re.findall(r"cid:(\d+)", cid_x)[0])
            char = self.cid_to_unicode.get(cid_num, None)
            if char is None:
                self.logger.warning(f"CID {cid_num} not found in the mapping.")
            return char
        except (IndexError, ValueError) as e:
            self.logger.error(f"Invalid CID format: {cid_x}. Error: {e}")
            return None

    def get_all_mappings(self):
        """
        获取所有的 CID 到 Unicode 的映射
        """
        return self.cid_to_unicode

if __name__ == "__main__":
    pdf_path = "example.pdf"
    target_font = "YourFontName"

    mapper = PdfCidToUnicodeMapper(pdf_path, target_font)
    mapper.extract_mapping()

    cid_x = "cid:1234"
    char = mapper.get_char_from_cid(cid_x)
    if char:
        print(f"Character for {cid_x}: {char}")
    else:
        print(f"Character for {cid_x} not found.")
    all_mappings = mapper.get_all_mappings()
    print(f"Total mappings found: {len(all_mappings)}")
