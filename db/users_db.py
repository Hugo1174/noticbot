import aiosqlite


# класс для работы с бд
class Database:
    def __init__(self, db_name='bot_db.db'):
        # инициализируем класс
        self.db_name = r'db/'+db_name

    async def create_database(self):
        # создание бд и таблиц, если их нет

        # подключаемя к бд с проверкой на ошибки
        async with aiosqlite.connect(self.db_name) as db:
            # создаём users
            await db.execute('''
                            CREATE TABLE IF NOT EXISTS Users (
                             user_id INTEGER PRIMARY KEY,
                             telegram_id TEXT UNIQUE NOT NULL,
                             user_name TEXT NOT NULL,
                             role TEXT CHECK(role IN ('student', 
                             'headman', 'admin')) NOT NULL,
                             group_id INTEGER,
                             FOREIGN KEY(group_id) REFERENCES Groups(group_id)
                             )
                             ''')
            await db.commit()

            # создаём groups
            await db.execute('''
                            CREATE TABLE IF NOT EXISTS Groups(
                             group_id INTEGER PRIMARY KEY,
                             faculty TEXT NOT NULL,
                             group_name TEXT NOT NULL,
                             headman_id INTEGER,
                             FOREIGN KEY (headman_id) REFERENCES Users(user_id)
                             )
                             ''')
            await db.commit()

            # Создаем assignments
            # изменить. Дату надо сохранять числом или строкой
            await db.execute('''
                            CREATE TABLE IF NOT EXISTS Assignments (
                            assignment_id INTEGER PRIMARY KEY,
                            group_id INTEGER NOT NULL,
                            title TEXT NOT NULL,
                            due_date DATETIME NOT NULL,
                            description TEXT,
                            FOREIGN KEY (group_id) REFERENCES Groups(group_id)
                        )
                        ''')
            await db.commit()

            # Создаем таблицу Tokens
            await db.execute('''
                            CREATE TABLE IF NOT EXISTS Tokens (
                            token_id INTEGER PRIMARY KEY,
                            token TEXT UNIQUE NOT NULL,
                            is_used BOOLEAN DEFAULT FALSE
                        )
                        ''')

            # Сохраняем изменения в базе данных
            await db.commit()

    # добавление юзера
    async def add_user(self, telegram_id: str, user_name: str, role: str, group_id=None):
        async with aiosqlite.connect(self.db_name) as db:
            try:
                await db.execute('''
                            INSERT INTO Users (telegram_id, user_name, role, group_id)
                             VALUES(?, ?, ?, ?)
                             ''', (str(telegram_id), user_name, role, group_id)
                             )
                await db.commit()
            except aiosqlite.IntegrityError as e:
                print(f"IntegrityError: {e}")
            # Обработка ошибки уникальности, например, пользователь уже существует
            except Exception as e:
                print(f"Error adding user: {e}")

    # удаление пользователя  
    async def delete_user(self, telegram_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("DELETE FROM Users WHERE telegram_id = ?", (telegram_id,))
            await db.commit()

    # получение инф-и о пользователе
    async def get_user(self, telegram_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT * FROM Users WHERE telegram_id = ?",
                                      (telegram_id,))
            return await cursor.fetchone()
    
    # поиск пользователей по группе
    async def search_user_by_group(self, group_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT * FROM Users WHERE group_id= ?",
                                      (group_id,))
            rows = await cursor.fetchall()
        
            #Преобразуем результаты в список словарей
            users = []
            for row in rows:
                user = {
                    "user_name": row[2],
                    "telegram_id": row[1]
               }
                users.append(user)
        
            return users


    # изменяем роль
    async def change_role(self, role: str, user_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            try:
                await db.execute('''UPDATE Users SET role = ? WHERE telegram_id = ?
                             ''', (role, user_id)
                             )
                await db.commit()
            except Exception as e:
                print(f"Error adding user: {e}")

    # изменяем роль
    async def add_group_id_to_headman(self, h_id: int, g_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            try:
                await db.execute('''UPDATE Users SET group_id = ? WHERE user_id = ?
                             ''', (g_id, h_id)
                             )
                await db.commit()
            except Exception as e:
                print(f"Error adding user: {e}")

    # создание группы
    async def add_group(self, faculty: str, group: str, id: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                            INSERT INTO Groups(faculty, group_name, headman_id)
                             VALUES(?, ?, ?)
                             ''', (faculty, group, id)
                             )
            await db.commit()

    # поиск группы
    async def search_group(self, faculty: str, group_name: str):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT * FROM Groups WHERE faculty = ? AND group_name = ?", (faculty, group_name))
            return await cursor.fetchone()
        
    # возврат групп    
    async def return_groups(self,):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT * FROM Groups")
            return await cursor.fetchone()

    # возврат группы    
    async def return_group(self, group_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT * FROM Groups WHERE group_id = ?", (group_id, ))
            return await cursor.fetchone()     
        
    # удаление группы    
    async def delete_group(self, faculty: str, group_name: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("DELETE FROM Groups WHERE group_name = ? AND faculty = ?", (group_name, faculty))
            await db.commit()
    
    # добавление события
    async def add_assignment(self, group_id: int, title: str, due_date, description: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO Assignments (group_id, title, due_date, description)
                VALUES (?, ?, ?, ?)
            ''', (group_id, title, due_date, description))
            await db.commit()

    # возвращает все события группы
    async def get_asignment(self, group_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT * FROM Assignments WHERE group_id= ?",
                                      (group_id,))
            rows = await cursor.fetchall()
        
            #Преобразуем результаты в список словарей
            events = []
            for row in rows:
                event = {
                    "assignment_id": row[0],
                    "group_id": row[1],
                    "title": row[2],
                    "due_date": row[3],
                    "description": row[4]
               }
                events.append(event)
        
            return events
        
    # возвращает события по дате
    async def get_events_by_date(self, search_date):
        async with aiosqlite.connect(self.db_name) as db:
            # Используем strftime для фильтрации по дате
            cursor = await db.execute('''
                SELECT * FROM Assignments 
                WHERE DATE(due_date) = ?
            ''', (search_date,))

            rows = await cursor.fetchall()

            # Преобразуем результаты в список словарей
            events = []
            for row in rows:
                event = {
                    "group_id": row[1],
                    "title": row[2],
                    "due_date": row[3],  # Это будет строка в формате 'YYYY-MM-DD HH:MM:SS'
                    "description": row[4]
                }
                events.append(event)

            return events

    # добавление токена
    async def add_token(self, token):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                            INSERT INTO Tokens(token, is_used)
                             VALUES(?, ?)
                             ''', (str(token), False)
                             )
            await db.commit()

    async def use_token(self, token):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                            UPDATE Tokens SET is_used = ? WHERE token = ?
                             ''', (True, str(token))
                             )
            await db.commit()

    # поиск токена
    async def search_token(self, token):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT * FROM Tokens WHERE token= ?", (str(token),))
            return await cursor.fetchone()
        
    
    async def number(self):
        async with aiosqlite.connect(self.db_name) as db:
            # Получаем количество пользователей
            cursor1 = await db.execute("SELECT Count(*) FROM Users")
            user_count = await cursor1.fetchone()  # Извлекаем результат
            user_count = user_count[0]  # Получаем значение из кортежа

            # Получаем количество групп
            cursor2 = await db.execute("SELECT Count(*) FROM Groups")
            group_count = await cursor2.fetchone()  # Извлекаем результат
            group_count = group_count[0]  # Получаем значение из кортежа

        return [user_count, group_count]  # Возвращаем список с количеством
        



    async def logging(self, i: int):
        async with aiosqlite.connect(self.db_name) as db:
            async with aiosqlite.connect(f'logs/bot_db{i}.db') as backup_db:
                await db.backup(backup_db)
                print(f'База данных успешно скопирована в bot_db{i}.db')




# добавление
# cursor.execute('INSERT INTO Users (user_id, username) 
#               VALUES (?, ?)', ('id телеги', 'first_name'))

# Удаляем пользователя(переделать для заметок)
# сursor.execute('DELETE FROM Users WHERE user_id = ?', ('id из телеги',))

''' извлечение данных
# Выбираем всех пользователей
cursor.execute('SELECT * FROM Users')
users = cursor.fetchall()

# Выводим результаты
for user in users:
    print(user)
'''
'''
Для получения информации там есть своя система фильтров
cur.execute("SELECT * FROM Users WHERE id = ?", (id, ))
all = cur.fetchone()
'''