import streamlit as st
import pandas as pd
import altair as alt

# =============================================
# КОНФИГУРАЦИЯ АУДИТОРИЙ
# =============================================

AUDITORIUM_101 = {
    "name": "Auditorium R503",
    "row_config": [
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
    ],
    "students": [
        "Иванов Иван Иванович", "Петров Петр Петрович", "Сидорова Анна Михайловна",
        "Кузнецов Дмитрий Сергеевич", "Смирнова Екатерина Викторовна", "Васильев Андрей Николаевич",
        "Попова Ольга Дмитриевна", "Новиков Александр Игоревич", "Федорова Мария Александровна",
        "Морозов Артем Олегович", "Волкова Юлия Сергеевна", "Алексеев Павел Денисович",
        "Лебедева Анастасия Романовна", "Козлов Игорь Вадимович", "Егорова Дарья Евгеньевна"
    ],
    "manual_assignments": {
        (1, 1): "Иванов Иван Иванович",
        (1, 2): "Петров Петр Петрович",
        (2, 1): "Сидорова Анна Михайловна"
    }
}

AUDITORIUM_201 = {
    "name": "Auditorium R505",
    "row_config": [
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        ["desk", "desk", "gap", "desk", "desk", "gap", "desk"],
        ["desk", "desk", "gap", "desk"],
    ],
    "students": [
        "Тарасов Никита Владимирович", "Андреева Вероника Станиславовна", "Борисов Максим Юрьевич",
        "Григорьева Елена Олеговна", "Дмитриев Константин Александрович", "Жукова Виктория Сергеевна",
        "Захаров Артемий Игоревич", "Ильина Марина Денисовна", "Крылов Станислав Валерьевич",
        "Ларина Ольга Павловна", "Миронов Денис Андреевич", "Николаева Анастасия Игоревна",
        "Осипов Владислав Артемович", "Павлова Кристина Романовна"
    ],
    "manual_assignments": {
        (1, 1): "Тарасов Никита Владимирович",
        (1, 2): "Андреева Вероника Станиславовна",
        (3, 1): "Борисов Максим Юрьевич"
    }
}

AUDITORIUMS = {
    "R501": AUDITORIUM_101,
    "R505": AUDITORIUM_201
}

# =============================================
# ФУНКЦИИ
# =============================================

def create_seating_chart(students, row_config, manual_assignments=None):
    if manual_assignments is None:
        manual_assignments = {}
    assignments = {}
    used = set()

    # 1. Ручные назначения
    for (r, s), name in manual_assignments.items():
        if 1 <= r <= len(row_config):
            max_seats = sum(2 for c in row_config[r-1] if c == "desk")
            if 1 <= s <= max_seats:
                assignments[(r, s)] = name
                used.add(name)
            else:
                st.error(f"CONFIG ERROR: место {(r, s)} отсутствует!")
        else:
            st.error(f"CONFIG ERROR: ряд {r} отсутствует!")

    # 2. Авто-рассадка оставшихся
    remaining = [x for x in students if x not in used]
    idx = 0
    for r_idx, cfg in enumerate(row_config, start=1):
        seats = sum(2 for c in cfg if c == "desk")
        for s in range(1, seats+1, 2):
            key = (r_idx, s)
            if key in assignments:
                continue
            if idx < len(remaining):
                assignments[key] = remaining[idx]
                idx += 1

    return assignments

# =============================================
# UI
# =============================================

st.set_page_config(layout="wide", page_title="Seating Chart")
st.title("Seating in the exam on differential equations")

choice = st.radio(
    "Choose auditorium",
    options=list(AUDITORIUMS.keys()),
    format_func=lambda k: AUDITORIUMS[k]["name"],
    horizontal=True
)

aud = AUDITORIUMS[choice]
row_config = aud["row_config"]
students = aud["students"]
manual = aud.get("manual_assignments", {})
name = aud["name"]

assignments = create_seating_chart(students, row_config, manual)

total_seats = sum(sum(2 for c in row if c == "desk") for row in row_config)
if len(students) > total_seats:
    st.error(f"⚠️ {len(students) - total_seats} студентов не уместились!")

st.subheader(f"{name}")

# Собираем DataFrame с учётом gap и tooltip
rows = []
max_cols = 0
for r_idx, cfg in enumerate(row_config, start=1):
    col_counter = 1
    seat_counter = 1
    for item in cfg:
        if item == "desk":
            for _ in range(2):
                student = assignments.get((r_idx, seat_counter), "")
                tooltip = f"{student} , seat {seat_counter}" if student else ""
                rows.append({
                    "row": r_idx,
                    "col": col_counter,
                    "tooltip": tooltip,
                    "occupied": bool(student)
                })
                seat_counter += 1
                col_counter += 1
        else:
            col_counter += 1
    max_cols = max(max_cols, col_counter - 1)

df = pd.DataFrame(rows)

# Добавляем селектор, который срабатывает на тач/клик:
selector = alt.selection_single(
    on="touchstart",      # можно также указать "click"
    fields=["row", "col"],
    empty="none"
)

chart = (
    alt.Chart(df)
    .mark_circle(size=300)
    .encode(
        x=alt.X("col:O", title=None, axis=alt.Axis(labels=False, ticks=False),
                scale=alt.Scale(domain=list(range(1, max_cols + 1)))),
        y=alt.Y("row:O", title="Row", sort="descending",
                axis=alt.Axis(labelAngle=0)),
        color=alt.condition(
            alt.datum.occupied,
            alt.value("red"),
            alt.value("lightgray")
        ),
        # Показываем tooltip из поля tooltip, но только для выбранной точки:
        opacity=alt.condition(selector, alt.value(1), alt.value(0.8)),
        tooltip=alt.Tooltip("tooltip:N", title="")
    )
    .add_selection(selector)      # <-- сюда
    .properties(height=len(row_config) * 50)
)

st.altair_chart(chart, use_container_width=True)

# Таблица с рассадкой
st.subheader("Student seating table")
table = [{"Name": nm, "Place": f"Row {r}, Seat {s}"} for (r, s), nm in assignments.items()]
st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
