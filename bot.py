import os
import re
import random
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

def roll_dice(num_dice: int, dice_size: int) -> list[int]:
    """
    Бросает num_dice костей dice_size-гранных и возвращает список результатов.
    """
    return [random.randint(1, dice_size) for _ in range(num_dice)]

def rollstats_command(update: Update, context: CallbackContext) -> None:
    """
    Команда !rollstats: Генерирует 6 статов по формуле 4d6d1.
    (4 броска d6, отбрасываем 1 худший результат).
    """
    stats = []
    for _ in range(6):
        rolls = roll_dice(4, 6)  # 4d6
        # Отбрасываем наименьший результат
        drops = sorted(rolls)
        drops.pop(0)  # убрать наименьший
        stat_value = sum(drops)
        stats.append(stat_value)
    update.message.reply_text(f"Ваши статы: {stats}")

def multiroll_command(update: Update, context: CallbackContext, text: str) -> None:
    """
    Команда !rr <iterations> <dice>
    Пример: !rr 3 1d20+5 -> трижды кидаем 1d20+5
    """
    parts = text.split()
    if len(parts) < 3:
        update.message.reply_text("Использование: !rr <количество> <выражение>. Пример: !rr 3 1d20+5")
        return
    
    try:
        iterations = int(parts[1])
    except ValueError:
        update.message.reply_text("Количество повторов должно быть числом.")
        return

    dice_expr = " ".join(parts[2:])  # всё, что после количества итераций, считаем выражением
    results = []
    for _ in range(iterations):
        res_text, val = parse_and_roll_expression(dice_expr)
        results.append(f"{res_text} = {val}")

    update.message.reply_text("\n".join(results))

def roll_command(update: Update, context: CallbackContext, text: str) -> None:
    """
    Универсальная команда !r [dice=1d20] ...
    Пример: !r 1d20+5
            !r 1d20+4 adv
            !r (1d8+2)*2
    """
    # Уберём '!r ' из начала
    expr = text[2:].strip()
    if not expr:
        expr = "1d20"  # если просто "!r" — используем бросок 1d20

    # Проверим на adv или dis
    advantage = False
    disadvantage = False
    # Для упрощения пусть adv/dis указывается в конце
    if expr.endswith(" adv"):
        advantage = True
        expr = expr.replace(" adv", "").strip()
    elif expr.endswith(" dis"):
        disadvantage = True
        expr = expr.replace(" dis", "").strip()

    # Обрабатываем выражение
    # (В этом примере парсер довольно простой, учитывает сумму, вычитание, скобки и т.д.)
    # Для полноты можно использовать готовые библиотеки или написать сложный парсер.

    # Если adv/dis применяем только к одному d20. (Упрощённая логика)
    if advantage or disadvantage:
        # Ищем 1d20 в выражении. Если его нет — просто игнорируем
        match = re.search(r"(\d+)d(\d+)", expr)
        if match:
            num_dice = int(match.group(1))
            dice_size = int(match.group(2))
            if num_dice == 1 and dice_size == 20:
                # Бросаем два раза
                first = random.randint(1, 20)
                second = random.randint(1, 20)
                chosen = max(first, second) if advantage else min(first, second)
                # Заменим "1d20" на выбранный результат
                expr_rolled = expr.replace("1d20", str(chosen), 1)
                # Теперь посчитаем оставшуюся математику
                rolled_text, total_val = evaluate_expression(expr_rolled)
                result_text = f"{expr} -> ADV/DIS [{first}, {second}] -> {chosen} -> {rolled_text} = {total_val}"
                update.message.reply_text(result_text)
                return

    # Если нет adv/dis или мы не нашли 1d20
    rolled_text, total_val = evaluate_expression(expr)
    result_text = f"{expr} = {rolled_text} = {total_val}"
    update.message.reply_text(result_text)

def parse_and_roll_expression(expr: str) -> tuple[str, int]:
    """
    Простая обёртка, которая возвращает (текст_броска, значение).
    """
    rolled_text, total_val = evaluate_expression(expr)
    return (rolled_text, total_val)

def evaluate_expression(expr: str) -> tuple[str, int]:
    """
    Пример очень упрощённого парсинга для выражения вида:
      1d20+5
      (1d8+2)*2
      2d6+1d4-2
    и т.п.
    Возвращает (строка с заменёнными бросками, итоговое_число).
    
    Ограничения:
      - Не поддерживает сложные операции (е, rr, ro, ra и т.д.),
      - Нормально работает только с +, -, *, / и скобками,
      - Для реальной игры рекомендуется использовать полноценный парсер (diceparser, pynacodice и пр.).
    """
    # Для безопасности НЕ используем прямой eval на пользовательском вводе.
    # Вместо eval — небольшой разбор через regex:
    # 1) Заменяем "XdY" на "(случайная_сумма)"
    # 2) Оставляем символы +, -, *, /, (, ) и цифры.
    
    # Находим все шаблоны "XdY"
    pattern = r"(\d+)d(\d+)"
    matches = re.findall(pattern, expr)
    rolled_expr = expr
    roll_map = {}  # для хранения промежуточных результатов

    for (x, y) in matches:
        num_dice = int(x)
        dice_size = int(y)
        results = roll_dice(num_dice, dice_size)
        sum_res = sum(results)
        # Сформируем строку вида "3+4" или просто "7" для замены
        # Но чтобы сохранить ясность, оформим как (3+4=7)
        results_str = "+".join(map(str, results))
        replace_str = f"({results_str}={sum_res})"
        # Заменим первое вхождение шаблона XdY на (3+4=7)
        rolled_expr = re.sub(rf"{x}d{y}", replace_str, rolled_expr, count=1)

    # Теперь rolled_expr содержит что-то вроде "(3+4=7)+5"
    # Упростим, чтобы превратить (3+4=7) в 7:
    # С помощью ещё одного regex найдём всё вида (X=Y) и заменим на Y
    rolled_expr = re.sub(r"\(([\d\+\-]+)=(\d+)\)", r"\2", rolled_expr)

    # Теперь rolled_expr — обычное арифметическое выражение, например "7+5".
    # Для вычисления используем eval, но предварительно проверим, что в строке
    # только цифры, скобки и операторы.
    safe_expr = re.sub(r"[^\d\+\-\*\/\(\)\.]", "", rolled_expr)  # убираем всё «лишнее»
    try:
        total_val = eval(safe_expr)
    except Exception:
        total_val = 0

    return (rolled_expr, total_val if isinstance(total_val, int) or isinstance(total_val, float) else 0)

def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Общий обработчик для текстовых сообщений, начинающихся с !
    """
    text = update.message.text.strip()
    if not text.startswith("!"):
        return  # если не начинается с !, игнорируем

    # Команда !rollstats
    if text.lower().startswith("!rollstats"):
        rollstats_command(update, context)
        return

    # Команда !rr
    if text.lower().startswith("!rr"):
        multiroll_command(update, context, text)
        return

    # Команда !r
    if text.lower().startswith("!r"):
        roll_command(update, context, text)
        return

    # Если команда начинается с !, но не совпадает с вышеуказанными:
    update.message.reply_text("Неизвестная команда. Доступны: !rollstats, !rr, !r")

def main():
    if TELEGRAM_TOKEN is None:
        print("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена.")
        return

    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    # Обрабатываем все сообщения (MessageHandler),
    # которые начинаются с '!' (команды Avrae-стиля).
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
