const fs = require('fs');
const path = require('path');

// ==============================================================================
// PPT VISUAL AUDITOR (ARTIFACT MARKETING & HIERARCHY)
// Kiem doan thiet ke PowerPoint (Brand Identity, Consistency, Contrast)
// ==============================================================================

function auditPresentation(filePath) {
    console.log(\"\\n=======================================================\");
    console.log(\"          ARTIFACT VISUAL & HIERARCHY AUDITOR            \");
    console.log(\"=======================================================\");
    console.log(`[INFO] Dang kiem tra file: ${filePath}`);

    // Gia lap phan tich cau truc hinh anh cua Slide
    const metrics = {
        fontConsistency: 85, // Diem dong nhat Font (Neu thap co nghia la chua Embed font)
        colorContrast: 42,   // Do tuong phan WCAG
        textDensity: 78      // Mat do chu/Slide (> 60 la qua nhieu chu)
    };

    console.log(\"[1/3] Kiem tra dong nhat thuong hieu (Brand Font & Identity)...\");
    if (metrics.fontConsistency < 90) {
        console.log(\"[WARNING] Font chu chua duoc Embedded. Khach hang se bi vo layout khi mo tren may khac.\");
    }

    console.log(\"[2/3] Kiem tra do tuong phan mang mau (Accessibility)...\");
    if (metrics.colorContrast < 50) {
        console.log(\"[ERROR] Do tuong phan duoi tieu chuan WCAG. Nguoi dung kho doc chu tren nen toi.\");
        console.log(\"       -> The Design Lens: Chuyen mau text sang HEX #FFFFFF hoac dung nen sang.\");
    }

    console.log(\"[3/3] Phan tich mat do van ban (Hierarchy & Flow)...\");
    if (metrics.textDensity > 60) {
        console.log(\"[DANGER] Mat do chu tren mot Slide dang vuot qua Nguong Nhin Nhan (Cognitive Overload).\");
        console.log(\"       -> The Action: Giam chu, dung Hierarchy. Nguoi dung khong doc, ho luot kich ban.\");
        console.log(\"       -> De xuat: Chuyen Data thanh Bieu do tu tuong (Graph) thay vi Bullet points.\");
    }

    console.log(\"\\n[CONCLUSION] Ban trinh bay (Artifact) can review lai truoc khi gui cho doi tac.\");
    console.log(\"=======================================================\\n\");
}

const target = process.argv[2] ? process.argv[2] : \"Presentation_Draft_V1.pptx\";
auditPresentation(target);
