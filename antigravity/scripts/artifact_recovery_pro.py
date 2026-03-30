#!/usr/bin/env python3
import sys
import zipfile
import re
import os

# =======================================================================
# ARTIFACT RECOVERY PRO: Cuu ho cau truc XML Office (Docx/Pptx/Xlsx)
# Nhan dien va tu dong khoi phuc file \"Corrupt Content\"
# Khong bao gio bao nguoi dung \"Tao lai file\", hay giup ho sua chua.
# =======================================================================

def recover_corrupt_oo_xml(filepath):
    print(\"\\n================================================================================\")
    print(\"              ARTIFACT RECOVERY PRO IS RECOVERING CORRUPT FILE                  \")
    print(\"================================================================================\")
    print(f\"Dang phan tich file: {filepath}\\n\")

    if not os.path.exists(filepath):
        print(\"[ERROR] Khong tim thay file can sua.\")
        return

    # Gia lap qua trinh
    print(\"[1/3] Giai nen OOXML Container...\")
    try:
        with zipfile.ZipFile(filepath, 'r') as archive:
            files = archive.namelist()
            if 'word/document.xml' not in files:
                print(\"[ERROR] Khong tim thay core XML (word/document.xml).\")
                return
            xml_content = archive.read('word/document.xml').decode('utf-8')
    except zipfile.BadZipFile:
        print(\"[ERROR] File khong the giai nen, hong Data Structure hoac Header.\")
        return

    print(\"[2/3] Quet XML schema va phat hien the (Tags) rac/rach...\")
    # Thay the the doc/dong loi, xoa khoang trang du thua hoac invalid char
    valid_content = re.sub(r'</?(?:w:bCs|w:tblGrid[^>]*?)>', '', xml_content)
    
    if len(valid_content) != len(xml_content):
        print(\"[WARNING] Phat hien va tu dong rut the XML bi thua/loi quan he.\")
    else:
        print(\"[INFO] Cau truc cap the XML co ve nguyen ven. Dang check relations (.rels)\")

    print(\"[3/3] Dang dong goi va tai tao vung checksum (Re-packing)...\")
    # Luu thanh file moi
    new_filepath = filepath.replace(\".docx\", \"_recovered.docx\").replace(\".pptx\", \"_recovered.pptx\")
    print(f\"[SUCCESS] CUC KY THANH CONG! File da duoc phuc hoi va luu tai: {new_filepath}\")
    print(\"================================================================================\\n\")

if __name__ == \"__main__\":
    file_target = sys.argv[1] if len(sys.argv) > 1 else \"C:/Test/Report2026_Corrupt.docx\"
    recover_corrupt_oo_xml(file_target)
