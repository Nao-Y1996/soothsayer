import pytest
from app.application.text_service import extract_enclosed, remove_enclosed

@pytest.mark.parametrize("input_text, expected", [
    ("This is <<an example>> string.", ["an example"]),
    ("<<Test>> only", ["Test"]),
    ("<<Multiple>> and <<patterns>> exist", ["Multiple", "patterns"]),
    ("No enclosed string", []),
    ("<<Empty>> <<>>", ["Empty", ""]),
    ("<<Nested <<inner>> outer>>", ["Nested <<inner>> outer"]),
    # Test case including newlines within the enclosed part
    ("Line one <<first\nsecond>> line end", ["first\nsecond"]),
    # Test case including newlines outside and within multiple enclosed parts
    ("<<Start>>\nMiddle <<End\nOf\nLine>>", ["Start", "End\nOf\nLine"])
])
def test_extract_enclosed(input_text, expected):
    assert extract_enclosed(input_text) == expected

@pytest.mark.parametrize("input_text, expected", [
    ("This is <<an example>> string.", "This is  string."),
    ("<<Test>> only", " only"),
    ("Before <<nested <<inner>> example>> after", "Before  after"),
    ("No enclosed string", "No enclosed string"),
    ("<<Empty>> <<>>", " "),
    ("Some <<multiple>> text <<to remove>> end", "Some  text  end"),
    ("<<Nested <<inner>> outer>>", ""),
    # Test case including newlines within the enclosed part
    ("Line one <<first\nsecond>> line end", "Line one  line end"),
    # Test case including newlines outside and within multiple enclosed parts
    ("<<Start>>\nMiddle <<End\nOf\nLine>>", "\nMiddle "),
    #
    ("""
<<position_table>>
2025年の占い（ひろしさん）
太陽・水星・火星が双子座なの！
超ポジティブで社交的な1年！
チャンスいっぱいだから、掴むだけ！
恋愛も仕事も最高潮なの！""",
"""

2025年の占い（ひろしさん）
太陽・水星・火星が双子座なの！
超ポジティブで社交的な1年！
チャンスいっぱいだから、掴むだけ！
恋愛も仕事も最高潮なの！""")

])
def test_remove_enclosed(input_text, expected):
    assert remove_enclosed(input_text) == expected