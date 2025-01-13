from pptx import Presentation

def remove_all_slides(prs: Presentation):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    for slide in slides:
        xml_slides.remove(slide)
    print(f"所有默认幻灯片已被移除，移除了{len(slides)}张幻灯片。")
