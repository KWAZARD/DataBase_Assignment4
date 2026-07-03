import uuid
import random
import psycopg2
from psycopg2 import Error
from psycopg2 import extras  # Необхідно для швидкої пакетної вставки

HOST = 'localhost'
USER = 'postgres'
PASSWORD = '_Rostik_281107_'
DATABASE = 'assignment4'
PORT = '5432'

def create_connection():
    try:
        connection = psycopg2.connect(
            host=HOST, port=PORT, user=USER, password=PASSWORD, dbname=DATABASE
        )
        print("Зв'язок з PostgreSQL встановлено успішно")
        return connection
    except Error as e:
        print(f"Помилка підключення: {e}")
        return None

def insert_data():
    connection = create_connection()
    if connection is None:
        return

    cursor = connection.cursor()

    # Списки для збереження згенерованих ID, щоб зв'язати таблиці між собою
    room_ids = [str(uuid.uuid4()) for _ in range(50)]
    course_ids = [str(uuid.uuid4()) for _ in range(30)]
    instructor_ids = [str(uuid.uuid4()) for _ in range(40)]
    group_ids = [str(uuid.uuid4()) for _ in range(60)]

    # 1. ЗАПОВНЕННЯ АУДИТОРІЙ (ROOMS) - 50 записів
    print("Генерація та вставка кімнат...")
    rooms_query = "INSERT INTO rooms (id, building, floor, number, display_name, seats_number) VALUES %s ON CONFLICT DO NOTHING"
    rooms_data = [
        (rid, f"Building {random.choice(['A', 'B', 'C', 'D'])}", random.randint(1, 5), random.randint(100, 599), f"Room-{random.randint(1,1000)}", random.randint(20, 150))
        for rid in room_ids
    ]
    extras.execute_values(cursor, rooms_query, rooms_data)

    # 2. ЗАПОВНЕННЯ КУРСІВ (COURSES) - 30 записів
    print("Генерація та вставка курсів...")
    courses_query = "INSERT INTO courses (id, course_display_short_name, course_display_full_name, course_description, lectures_num, practices_num) VALUES %s ON CONFLICT DO NOTHING"
    courses_data = [
        (cid, f"CS-{i}", f"Course Full Name {i}", f"Description for course {i}", random.randint(20, 40), random.randint(10, 30))
        for i, cid in enumerate(course_ids)
    ]
    extras.execute_values(cursor, courses_query, courses_data)

    # 3. ЗАПОВНЕННЯ ВИКЛАДАЧІВ (INSTRUCTORS) - 40 записів
    print("Генерація та вставка викладачів...")
    instructors_query = "INSERT INTO instructors (id, first_name, last_name, email, phone, active) VALUES %s ON CONFLICT DO NOTHING"
    instructors_data = [
        (iid, f"InstructorFN_{i}", f"InstructorLN_{i}", f"instructor_{i}@university.com", f"+38050{random.randint(1000000, 9999999)}", True)
        for i, iid in enumerate(instructor_ids)
    ]
    extras.execute_values(cursor, instructors_query, instructors_data)

    # 4. РОЗКЛАД СЛОТІВ (LESSONS_SCHEDULE) - 6 занять на день
    print("Генерація та вставка слотів часу...")
    lessons_schedule_query = "INSERT INTO lessons_schedule (id, start_time, end_time) VALUES %s ON CONFLICT DO NOTHING"
    lessons_schedule_data = [
        (1, "08:30:00", "10:05:00"),
        (2, "10:25:00", "12:00:00"),
        (3, "12:20:00", "13:55:00"),
        (4, "14:15:00", "15:50:00"),
        (5, "16:10:00", "17:45:00"),
        (6, "18:00:00", "19:35:00")
    ]
    extras.execute_values(cursor, lessons_schedule_query, lessons_schedule_data)

    # 5. ЗВ'ЯЗОК ВИКЛАДАЧІВ І КУРСІВ (INSTRUCTORS_COURSES)
    print("Генерація зв'язків викладач-курс...")
    ic_query = "INSERT INTO instructors_courses (instructor_id, course_id) VALUES %s ON CONFLICT DO NOTHING"
    ic_data = list({(random.choice(instructor_ids), random.choice(course_ids)) for _ in range(80)})
    extras.execute_values(cursor, ic_query, ic_data)

    # 6. ГРУПИ КУРСІВ (STUDENTS_COURSE_GROUPS) - 60 записів
    print("Генерація та вставка груп...")
    scg_query = "INSERT INTO students_course_groups (id, course_id) VALUES %s ON CONFLICT DO NOTHING"
    scg_data = [(gid, random.choice(course_ids)) for gid in group_ids]
    extras.execute_values(cursor, scg_query, scg_data)

    # 7. ВЕЛИКА ГЕНЕРАЦІЯ: СТУДЕНТИ (STUDENTS) - 500 000 записів!
    # Щоб не перевантажувати оперативну пам'ять, вставляємо частинами (чанками) по 50 000
    print("Генерація та вставка 500,000 студентів (це займе трохи часу)...")
    students_query = """
    INSERT INTO students (id, first_name, last_name, email, phone, course, educational_degree, speciality, active)
    VALUES %s ON CONFLICT (id) DO NOTHING
    """
    
    total_students = 500000
    chunk_size = 50000
    student_ids = []

    first_names = ["Oleksandr", "Maria", "Ivan", "Anna", "Dmytro", "Olena", "Serhiy", "Yulia", "Andriy", "Natalia"]
    last_names = ["Shevchenko", "Boyko", "Kovalenko", "Bondarenko", "Tkachenko", "Kravchenko", "Oliynyk", "Moroz"]
    degrees = ["Bachelor", "Master"]
    specialities = ["Computer Science", "Software Eng", "Cybersecurity", "Applied Math"]

    for chunk_start in range(0, total_students, chunk_size):
        students_data = []
        for i in range(chunk_start, chunk_start + chunk_size):
            s_id = str(uuid.uuid4())
            student_ids.append(s_id) # Зберігаємо для наступного кроку
            
            email = f"student_{i}@example.com" # Гарантовано унікальний email для тесту індексів
            phone = f"+38067{random.randint(1000000, 9999999)}"
            
            students_data.append((
                s_id,
                random.choice(first_names),
                random.choice(last_names),
                email,
                phone,
                random.randint(1, 4),
                random.choice(degrees),
                random.choice(specialities),
                True
            ))
        extras.execute_values(cursor, students_query, students_data, page_size=2000)
        print(f" Вставлено {chunk_start + chunk_size} студентів...")

    # 8. ВЕЛИКА ГЕНЕРАЦІЯ: СТУДЕНТИ В ГРУПАХ (STUDENTS_COURSE_GROUP_STUDENTS) - 500 000 записів
    print("Прив'язка 500,000 студентів до груп...")
    scgs_query = "INSERT INTO students_course_group_students (student_id, group_id) VALUES %s ON CONFLICT DO NOTHING"
    
    for chunk_start in range(0, len(student_ids), chunk_size):
        scgs_data = [
            (s_id, random.choice(group_ids))
            for s_id in student_ids[chunk_start : chunk_start + chunk_size]
        ]
        extras.execute_values(cursor, scgs_query, scgs_data, page_size=2000)
        print(f" Зв'язано {chunk_start + chunk_size} студентів з групами...")

    # 9. РОЗКЛАД (SCHEDULE) - 1000 записів
    print("Генерація та вставка розкладу...")
    schedule_query = """
    INSERT INTO schedule (id, course_id, instructor_id, students_course_group_id, week_day, lesson_schedule_id, room_id)
    VALUES %s ON CONFLICT (id) DO NOTHING
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    schedule_data = []
    
    # Використовуємо set, щоб уникнути конфліктів унікальності унікального ключа розкладу
    unique_combinations = set()
    sched_id = 1
    
    while len(schedule_data) < 1000:
        c_id = random.choice(course_ids)
        i_id = random.choice(instructor_ids)
        g_id = random.choice(group_ids)
        r_id = random.choice(room_ids)
        
        combo = (c_id, i_id, g_id, r_id)
        if combo not in unique_combinations:
            unique_combinations.add(combo)
            schedule_data.append((
                sched_id, c_id, i_id, g_id, random.choice(days), random.randint(1, 6), r_id
            ))
            sched_id += 1

    extras.execute_values(cursor, schedule_query, schedule_data)

    # Фіксуємо транзакцію
    connection.commit()
    cursor.close()
    connection.close()
    print("\n[УСПІХ] Базу даних успішно наповнено 500,000+ рядками!")

if __name__ == "__main__":
    insert_data()