from string import punctuation

def check_lot(check:str, string_type:str, number_min:int, number_max:int):
    length = len(check)
    check = check.translate(str.maketrans('', '', punctuation))
    check = check.replace(" ", "")
    if string_type == "letters":
        if check.isalpha(): 
            if length >= number_min and length <= number_max:
                return True
            else: return f"Сообщение должно содержать от {number_min} до {number_max} символа/-ов"
        else: return "В сообщении должны быть только буквы"
    if string_type == "numbers":
        if check.isdigit(): 
            if length >= number_min and length <= number_max:
                return True
            else: return f"Сообщение должно содержать от {number_min} до {number_max} символа/-ов"
        else: return "В сообщении должны быть только цифры"
    if string_type == "letters and numbers":
        if length >= number_min and length <= number_max:
                return True
        else: return f"Сообщение должно содержать от {number_min} до {number_max} символа/-ов"
