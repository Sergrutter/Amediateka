import sqlite3
import io
import sys

from PyQt6 import QtCore, QtWidgets
from PyQt6 import uic
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QMainWindow, QLineEdit, QPushButton, QApplication, QLabel, QWidget,
    QTextEdit, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QScrollArea,
    QTableWidget, QTableWidgetItem
)

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
class Amediateka(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.watched_movies = []
        self.username = "Гость"

    def initUI(self):
        self.setGeometry(200, 100, 1200, 600)
        self.setWindowTitle('Amediateka - Поиск фильмов')

        self.search_window = QLineEdit(self)
        self.search_window.setPlaceholderText("Введите название фильма или сериала")
        self.search_window.setGeometry(20, 20, 960, 40)
        self.search_window.setFont(QFont("Arial", 14))

        self.search_button = QPushButton('🔎', self)
        self.search_button.setGeometry(1000, 20, 50, 40)
        self.search_button.clicked.connect(self.film_info)

        self.parametrs_button = QPushButton('🎚️', self)
        self.parametrs_button.setGeometry(1060, 20, 50, 40)
        self.parametrs_button.clicked.connect(self.search_parametrs)

        self.result_area = QFrame(self)
        self.result_area.setGeometry(20, 80, 1260, 600)
        self.result_area.setStyleSheet("border: 1px solid gray; background-color: #f5f5f5;")
        self.result_area.setLayout(QVBoxLayout())

        self.center_image = QLabel(self)
        self.center_image.setPixmap(
            QPixmap("Amediateka.jpg").scaled(1000, 500, Qt.AspectRatioMode.KeepAspectRatio))
        self.center_image.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.result_area.layout().addWidget(self.center_image)

        self.registration_button = QPushButton("Регистрация", self)
        self.registration_button.resize(120, 30)
        self.registration_button.move(1140, 25)
        self.registration_button.clicked.connect(self.open_registration_window)

        self.user_label = QLabel("Гость", self)
        self.user_label.move(1200, 0)
        self.user_label.resize(200, 30)

        self.watched_area = QFrame(self)
        self.watched_area.setGeometry(1000, 80, 280, 600)
        self.watched_area.setStyleSheet("border: 1px solid gray; background-color: #ffffff;")
        self.watched_area.setLayout(QVBoxLayout())
        self.watched_area.layout().addWidget(QLabel("Просмотренные фильмы:", self))

        self.recommendations_area = QFrame(self)
        self.recommendations_area.setGeometry(20, 450, 980, 230)
        self.recommendations_area.setStyleSheet("border: 1px solid gray; background-color: #ffffff;")
        self.recommendations_area.setLayout(QVBoxLayout())
        self.recommendations_label = QLabel("Рекомендуем посмотреть:", self)
        self.recommendations_label.setFont(QFont("Arial", 12))
        self.recommendations_area.layout().addWidget(self.recommendations_label)


    def film_info(self):
        title = self.search_window.text().strip()
        username = self.user_label.text().strip().replace('Пользователь:', '')
        if title and username:
            self.film_form = FilmInfo(title, username)
            self.film_form.movie_watched.connect(self.add_to_watched)
            self.film_form.show()
        else:
            QMessageBox.warning(self, "Ошибка", "Введите название фильма для поиска")

    def search_parametrs(self):
        username = self.user_label.text().strip().replace('Пользователь:', '')
        self.search_form = Parametrs(username)
        self.search_form.show()

    def update_results(self, results):
        layout = self.result_area.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        for result in results:
            lbl = QLabel(result, self)
            layout.addWidget(lbl)

    def open_registration_window(self):
        self.registration_window = RegistrationWindow("C:\\Users\\Serg\\Downloads\\films_db.sqlite")
        self.registration_window.registration_successful.connect(self.update_user_label)
        self.registration_window.show()

    def update_user_label(self, username):
        self.username = username
        self.user_label.setText(f"Пользователь: {username}")
        self.registration_button.hide()
        self.user_label.move(1150, 24)

        self.load_watched_movies()
        self.load_recommendations()

    def add_to_watched(self, movie_title):
        if movie_title not in self.watched_movies:
            self.watched_movies.append(movie_title)

            try:
                con = sqlite3.connect("C:\\Users\\Serg\\Downloads\\films_db.sqlite")
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO watched_movies (username, movie_title) VALUES (?, ?)",
                    (self.username, movie_title)
                )
                con.commit()
                con.close()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить просмотренный фильм: {e}")

            label = QLabel(movie_title, self)
            self.watched_area.layout().addWidget(label)

    def load_watched_movies(self):
        try:
            con = sqlite3.connect("C:\\Users\\Serg\\Downloads\\films_db.sqlite")
            cur = con.cursor()
            cur.execute(
                "SELECT movie_title FROM watched_movies WHERE username = ?",
                (self.username,)
            )
            movies = cur.fetchall()
            con.close()

            for movie_title, in movies:
                self.watched_movies.append(movie_title)
                label = QLabel(movie_title, self)
                self.watched_area.layout().addWidget(label)

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить просмотренные фильмы: {e}")

    def get_recommendations(self):
        try:
            con = sqlite3.connect("C:\\Users\\Serg\\Downloads\\films_db.sqlite")
            cur = con.cursor()
            cur.execute(
                """SELECT DISTINCT f.genre 
                   FROM films f
                   JOIN watched_movies wm ON f.title = wm.movie_title
                   WHERE wm.username = ?""",
                (self.username,)
            )
            genres = [row[0] for row in cur.fetchall()]

            if not genres:
                return []

            query = f"""
                SELECT title 
                FROM films 
                WHERE genre IN ({','.join('?' * len(genres))})
                AND title NOT IN (
                    SELECT movie_title 
                    FROM watched_movies 
                    WHERE username = ?
                )
                LIMIT 10
            """
            cur.execute(query, (*genres, self.username))
            recommendations = [row[0] for row in cur.fetchall()]
            con.close()
            return recommendations

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить рекомендации: {e}")
            return []

    def load_recommendations(self):
        recommendations = self.get_recommendations()

        layout = self.recommendations_area.layout()
        for i in reversed(range(1, layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if recommendations:
            for title in recommendations:
                label = QLabel(title, self)
                label.setOpenExternalLinks(False)
                label.linkActivated.connect(lambda t=title: self.open_film_info(t))
                layout.addWidget(label)
        else:
            no_recommendations_label = QLabel("Рекомендации отсутствуют.", self)
            layout.addWidget(no_recommendations_label)

    def open_film_info(self, title):
        film_info_window = FilmInfo(title, self.username)
        film_info_window.movie_watched.connect(self.add_to_watched)
        film_info_window.show()
        self.film_info_window = film_info_window


class FilmInfo(QMainWindow):
    movie_watched = pyqtSignal(str)

    def __init__(self, title, username="Гость"):
        super().__init__()
        self.title = title
        self.username = username
        self.film_id = title
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle(f'Информация о фильме: {self.title}')

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.title_label = QLabel(f"Название: {self.title}")
        layout.addWidget(self.title_label)

        info_layout = QHBoxLayout()
        layout.addLayout(info_layout)

        self.image = QLabel()
        self.image.setFixedSize(350, 500)
        info_layout.addWidget(self.image)

        self.details_layout = QVBoxLayout()
        info_layout.addLayout(self.details_layout)


        self.year_label = QLabel("Год выпуска:")
        self.year_label.move(1100, 0)
        self.details_layout.addWidget(self.year_label)
        self.duration_label = QLabel("Продолжительность:")
        self.details_layout.addWidget(self.duration_label)
        self.genre_label = QLabel("Жанр:")
        self.details_layout.addWidget(self.genre_label)
        self.reviews_label = QLabel("Отзывы:", self)
        layout.addWidget(self.reviews_label)

        description_layout = QHBoxLayout()
        layout.addLayout(description_layout)

        self.description_text_edit = QTextEdit(self)
        self.description_text_edit.setReadOnly(True)
        self.description_text_edit.setStyleSheet("background-color: #f5f5f5;")
        self.description_text_edit.setFixedWidth(600)
        description_layout.addStretch()
        description_layout.addWidget(self.description_text_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        description_layout.addStretch()

        self.reviews_area = QScrollArea(self)
        self.reviews_widget = QWidget()
        self.reviews_layout = QVBoxLayout(self.reviews_widget)
        self.reviews_area.setWidget(self.reviews_widget)
        self.reviews_area.setWidgetResizable(True)
        layout.addWidget(self.reviews_area)

        self.add_review_label = QLabel("Добавьте отзыв:", self)
        layout.addWidget(self.add_review_label)

        self.trailer_button = QPushButton("Трейлер ▶️", self)
        self.trailer_button.setGeometry(1100, 150, 120, 40)
        self.trailer_button.clicked.connect(self.open_video_player)

        self.review_input = QTextEdit(self)
        layout.addWidget(self.review_input)

        self.submit_button = QPushButton("Сохранить отзыв", self)
        self.submit_button.clicked.connect(self.save_review)
        layout.addWidget(self.submit_button)

        self.watch_button = QPushButton("Добавить в просмотренные", self)
        self.watch_button.clicked.connect(self.mark_as_watched)
        layout.addWidget(self.watch_button)

        con = sqlite3.connect("C:\\Users\\Serg\\Downloads\\films_db.sqlite")
        cur = con.cursor()

        result = cur.execute(
            f"""SELECT f.poster, f.year, f.duration, g.title, f.description
         FROM films f
         LEFT JOIN genres g ON f.genre = g.id
         WHERE f.title LIKE ?""",
            (self.title,)
        ).fetchone()

        if result:

            poster, year, duration, genre, description = result

            self.year_label.setText(f"Год выпуска: {year}")
            self.duration_label.setText(f"Продолжительность: {duration} минут")
            self.genre_label.setText(f"Жанр: {genre}")

            if poster:
                with open('afisha.jpg', 'wb') as f:
                    f.write(poster)
                pixmap = QPixmap('afisha.jpg')
                self.image.setPixmap(pixmap)

            self.description_text_edit.setText(description)
        else:
            self.title_label.setText("Фильм не найден")
            self.year_label.setText("")
            self.duration_label.setText("")
            self.genre_label.setText("")
            self.description_text_edit.setText("Описание не найдено.")

        con.close()

    def load_reviews(self):
        try:
            con = sqlite3.connect("C:\\Users\\Serg\\Downloads\\films_db.sqlite")
            cur = con.cursor()

            cur.execute("SELECT username, review FROM reviews WHERE film_id = ?", (self.film_id,))
            reviews = cur.fetchall()
            con.close()

            for i in reversed(range(self.reviews_layout.count())):
                widget = self.reviews_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            if reviews:
                for username, review in reviews:
                    review_label = QLabel(f"<b>{username}:</b> {review}", self)
                    self.reviews_layout.addWidget(review_label)
            else:
                no_reviews_label = QLabel("Отзывов пока нет.", self)
                self.reviews_layout.addWidget(no_reviews_label)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить отзывы: {e}")

    def save_review(self):
        review_text = self.review_input.toPlainText().strip()

        if not review_text:
            QMessageBox.warning(self, "Ошибка", "Отзыв не может быть пустым!")
            return

        try:
            con = sqlite3.connect("C:\\Users\\Serg\\Downloads\\films_db.sqlite")
            cur = con.cursor()

            cur.execute(
                "INSERT INTO reviews (film_id, username, review) VALUES (?, ?, ?)",
                (self.film_id, self.username, review_text)
            )
            con.commit()
            con.close()

            QMessageBox.information(self, "Успех", "Отзыв успешно сохранён!")
            self.review_input.clear()
            self.load_reviews()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отзыв: {e}")

    def open_video_player(self):
        try:
            video_url = get_video_url_from_db(self.title)
            if not video_url:
                QMessageBox.warning(self, "Ошибка", "Трейлер для данного фильма не найден.")
                return

            self.video_player = VideoPlayer(video_url)
            self.video_player.show()

        except ValueError as ve:
            QMessageBox.warning(self, "Ошибка", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть видеоплеер: {e}")

    def mark_as_watched(self):
        self.movie_watched.emit(self.title)
        QMessageBox.information(self, "Информация", f"Фильм '{self.title}' добавлен в просмотренные.")
        self.close()


class Parametrs(QMainWindow):
    def __init__(self, username=None):
        super().__init__()
        self.db_path = "C:\\Users\\Serg\\Downloads\\films_db.sqlite"
        self.username = username

        uic.loadUi("parametr.ui", self)

        self.applyButton.clicked.connect(self.perform_search)

        self.Duration.valueChanged.connect(self.update_duration_display)

        self.Name.setText("")
        self.Year.setValue(0)
        self.Genre.setCurrentIndex(-1)
        self.Type.setCurrentIndex(-1)

    def update_duration_display(self, value):
        self.DurationDisplay.display(value)

    def perform_search(self):
        title = self.Name.text().strip()
        year = self.Year.value()
        duration = self.Duration.value()
        genre = self.Genre.currentText()
        film_type = self.Type.currentText()

        query = "SELECT id, title FROM films WHERE 1=1"
        params = []

        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")
        if year and year != 1900:
            query += " AND year = ?"
            params.append(year)
        if duration and duration != 5:
            query += " AND duration <= ?"
            params.append(duration)
        if genre:
            query += " AND genre = (SELECT id FROM genres WHERE title LIKE ?)"
            params.append(genre.lower())
        if film_type:
            query += " AND type = (SELECT id FROM ForS WHERE title LIKE ?)"
            params.append(film_type.lower())

        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            cur.execute(query, params)
            results = cur.fetchall()
            con.close()

            if results:
                self.show_results(results)
            else:
                QMessageBox.information(self, "Результаты поиска", "Фильмы по заданным параметрам не найдены.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить поиск: {e}")

    def show_results(self, results):
        results_window = QTableWidget()
        results_window.setWindowTitle("Результаты поиска")
        results_window.setColumnCount(2)
        results_window.setRowCount(len(results))
        results_window.setHorizontalHeaderLabels(["ID", "Название"])

        for row_idx, row_data in enumerate(results):
            for col_idx, col_data in enumerate(row_data):
                results_window.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

        results_window.resize(500, 300)
        results_window.show()

        results_window.cellDoubleClicked.connect(lambda row, col: self.open_film_info(results[row][1]))
        self.results_window = results_window

    def open_film_info(self, title):
        self.film_info_window = FilmInfo(title)
        self.film_info_window.show()


class RegistrationWindow(QMainWindow):
    registration_successful = pyqtSignal(str)

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 400, 200)
        self.setWindowTitle("Регистрация")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.login_label = QLabel("Логин:", self)
        layout.addWidget(self.login_label)
        self.login_input = QLineEdit(self)
        layout.addWidget(self.login_input)

        self.password_label = QLabel("Пароль:", self)
        layout.addWidget(self.password_label)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.register_button = QPushButton("Зарегистрироваться", self)
        self.register_button.clicked.connect(self.register_user)
        layout.addWidget(self.register_button)

    def register_user(self):
        username = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Логин и пароль не могут быть пустыми!")
            return

        try:
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()

            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            con.commit()
            con.close()

            QMessageBox.information(self, "Успех", "Пользователь успешно зарегистрирован!")
            self.registration_successful.emit(username)
            self.close()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Такой логин уже существует!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось зарегистрировать пользователя: {e}")


class VideoPlayer(QMainWindow):
    def __init__(self, urly):
        super().__init__()
        self.urly = urly

        self.setWindowTitle("Video Player")
        self.resize(800, 600)

        self.video_widget = QVideoWidget()

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        self.audio_output.setVolume(1)

        self.player.setSource(QUrl(urly))

        play_button = QPushButton("Play")
        play_button.clicked.connect(self.player.play)

        pause_button = QPushButton("Pause")
        pause_button.clicked.connect(self.player.pause)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.player.stop)

        layout = QVBoxLayout()
        layout.addWidget(self.video_widget)
        layout.addWidget(play_button)
        layout.addWidget(pause_button)
        layout.addWidget(stop_button)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


def get_video_url_from_db(title):
    try:
        conn = sqlite3.connect("C:\\Users\\Serg\\Downloads\\films_db.sqlite")
        cursor = conn.cursor()
        cursor.execute("SELECT treiler FROM films WHERE title = ?", (title,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return result[0]
        else:
            raise ValueError("Трейлер для данного фильма не найден.")
    except Exception as e:
        raise ValueError(f"Ошибка при извлечении URL: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Amediateka()
    ex.show()
    sys.exit(app.exec())
