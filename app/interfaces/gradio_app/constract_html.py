def h1_tag(text: str) -> str:
    return f"<h1>{text}</h1>"


def h2_tag(text: str) -> str:
    return f"<h2>{text}</h2>"


def div_center_bold_text(text: str, size: int = 18) -> str:
    """
    以下の構造のhtmlを返す
    <div style='text-align: center; font-size: {size}px; font-weight: bold;'>
        {text}
    </div>
    """
    return f"<div style='text-align: center; font-size: {size}px; font-weight: bold;'>{text}</div>"
