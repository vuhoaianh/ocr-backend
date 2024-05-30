from difflib import SequenceMatcher


CLS_MAP = {
    0: "ID",
    1: "Họ và tên",
    2: "Ngày sinh",
    3: "Giới tính",
    4: "Quốc tịch",
    5: "Quê quán",
    6: "Có giá trị đến",
    7: "thuong_tru_1",
    8: "thuong_tru_2",
}


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def find_similar_strings(patterns, text, threshold=0.8):
    matches = []

    for pattern in patterns:
        pattern_length = len(pattern)

        for i in range(len(text) - pattern_length + 1):
            substring = text[i:i + pattern_length]
            sim = similarity(pattern, substring)
            if sim >= threshold:
                matches.append(substring)

    return matches


def get_right_of_substring(original_string, substring):
    index = original_string.find(substring)
    if index == -1:
        return "Substring not found in the original string."
    else:
        right_part = original_string[index + len(substring):]
        return right_part


def check_date(string):
    pattern = ["Ngày", "Tháng", "Năm"]
    matches = find_similar_strings(pattern, string)
    if len(matches) > 1:
        return True
    else:
        return False


def check_key_similarity(string, pattern_list, threshold=0.9):
    for pattern in pattern_list:
        similarity_score = similarity(string, pattern)
        if similarity_score >= threshold:
            return pattern
    return None


def line_check(line1, line2, threshold=10):
    if abs(line1[1] - line2[1]) < threshold:
        if abs(line1[3] - line2[3]) < threshold:
            return True
    return False


def merge_lines(key, txt, lines, threshold):
    if similarity("Nội dung thanh toán", key) > threshold:
        for line in lines:
            if similarity("Số tiền", line) < 0.6:
                txt += f" {line}"
            else:
                break
    return txt


def clean_text(txt):
    txt = txt.replace(":", "")
    txt = txt.strip()
    return txt
