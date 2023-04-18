import flask
from flask import render_template, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from model import db, Lecture, app, User, Test, Question

app.app_context().push()
db.create_all()
login_manager = LoginManager(app)
login_manager.login_view = '/'


def insert_admin():
    if db.session.query(User).filter(User.username == "admin").first() is None:
        user = User(username="admin", name="admin",
                    email="admin", role="admin")
        user.set_password("admin")
        db.session.add(user)
        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route('/recommendations', methods=['POST'])
@login_required
def show_recommendations_page():
    import random
    lectures_list = db.session.query(Lecture).filter(Lecture.lvl <= current_user.user_lvl).all()
    tests_list = db.session.query(Test).filter(Test.lvl <= current_user.user_lvl).all()
    lecture = None
    test = None
    if len(lectures_list) > 0:
        lecture = random.choice(lectures_list)
    if len(tests_list) > 0:
        test = random.choice(tests_list)
    return render_template("recommendations.html", user=current_user, lecture=lecture,
                           test=test)


@app.route('/addQuestionInTest', methods=['POST'])
def add_question_in_test():
    test_id = request.form.get("testId")
    test = db.session.query(Test).filter(Test.id == test_id).first()
    if test:
        question = Question(title=request.form.get(
            "questionName"), author=test)
        question.possible_answers = ""
        for i in range(1, 7):
            if request.form.get(f"answer{i}") != "":
                question.possible_answers += request.form.get(
                    f"answer{i}") + ","
        question.true_answer = request.form.get("trueAnswer")
        db.session.add(question)
        db.session.commit()
        return show_admin_panel(message="Вопрос успешно добавлен")
    else:
        return show_admin_panel(message="Ошибка")


@app.route('/addTest', methods=['POST'])
def add_test():
    if not db.session.query(Test).filter(Test.name == request.form.get("name")).first():
        test = Test(name=request.form.get("name"))
        if request.form.get("lvl") != "":
            test.lvl = int(request.form.get("lvl"))
            db.session.add(test)
            db.session.commit()
        if request.form.get("attemptsCount") != "":
            test.attempts_count = int(request.form.get("attemptsCount"))
            db.session.add(test)
            db.session.commit()
        db.session.add(test)
        db.session.commit()
        return show_admin_panel(message="Тест успешно добавлен")
    else:
        return show_admin_panel(message="Тест с таким именем уже существует !!!")


@app.route('/addLecture', methods=['POST'])
def add_lecture():
    title = request.form.get('title')
    text = request.form.get('text')
    image_path = request.form.get('image_path')
    lecture = Lecture(title=title, text=text, image_path=image_path)
    if request.form.get("lvl") != "":
        lecture.lvl = int(request.form.get("lvl"))
        db.session.add(lecture)
        db.session.commit()
    db.session.add(lecture)
    db.session.commit()
    return render_template("admin.html", message="Лекция успешно добавлена")


@app.route('/')
def index(message=""):
    insert_admin()
    if current_user.is_authenticated:
        return show_profile()
    else:
        return render_template('login.html', message=message)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if flask.request.method == 'POST':
        user = User(username=request.form.get("username"), name=request.form.get("name"),
                    email=request.form.get("email"))
        user.set_password(request.form.get("password"))
        db.session.add(user)
        db.session.commit()
        return render_template('login.html', message="Успешная регистрация")
    else:
        return render_template('registration.html')


@app.route('/show_test_result<test_id>', methods=['POST'])
@login_required
def show_test_result(test_id):
    test = db.session.query(Test).filter(
        Test.id == test_id).first()
    test.attempts_count -= 1
    question = test.questions.filter(
        Question.id == current_user.current_question_id).first()
    if request.form.get("answer") == question.true_answer:
        test.true_answers_count += 1
        db.session.add(test)
        db.session.commit()
    test_result = test.true_answers_count / test.questions.count()
    if test_result < 0.25:
        current_user.user_lvl -= 5
    elif test_result < 0.5:
        pass
    elif test_result > 0.7:
        current_user.user_lvl += 5
    elif test_result > 0.9:
        current_user.user_lvl += 10
    db.session.add(test)
    db.session.commit()
    return render_template('test_result.html', test=test,
                           message=f"{test.true_answers_count}/{test.questions.count()}, "
                                   f"{round(test_result * 100, 2)}%")


@app.route('/show_test<test_id>', methods=['POST'])
@login_required
def show_test(test_id):
    current_user.current_test_id = test_id
    test = db.session.query(Test).filter(
        Test.id == test_id).first()
    test.complete_questions_count = 0
    test.true_answers_count = 0
    current_user.current_question_id = test.questions.all()[0].id
    db.session.add(test)
    db.session.add(current_user)
    db.session.commit()
    return show_test_question(current_user.current_question_id)


@app.route('/show_test_question<question_id>', methods=['POST'])
@login_required
def show_test_question(question_id):
    test = db.session.query(Test).filter(
        Test.id == current_user.current_test_id).first()
    question = test.questions.filter(
        Question.id == current_user.current_question_id).first()
    if request.form.get("answer") == question.true_answer:
        test.true_answers_count += 1
        db.session.add(test)
    current_user.current_question_id = question_id
    db.session.add(current_user)
    db.session.commit()
    question = test.questions.filter(
        Question.id == current_user.current_question_id).first()
    answers = [i for i in question.possible_answers.split(",") if i != ""]
    test.complete_questions_count += 1
    db.session.add(test)
    db.session.commit()
    try:
        test.questions[test.complete_questions_count]
        return render_template('question.html', question_title=question.title, answers=answers,
                               post_url=f"/show_test_question{test.questions[test.complete_questions_count].id}",
                               button_text="Далее")
    except IndexError:
        return render_template('question.html', question_title=question.title, answers=answers,
                               post_url=f"/show_test_result{current_user.current_test_id}", button_text="Завершить")


@app.route('/complete_test<test_id>', methods=['POST'])
@login_required
def complete_test(test_id):
    test = db.session.query(Test).filter(
        Test.id == current_user.current_test_id).first()
    test.questions.filter(
        Question.id == current_user.current_question_id).first()
    test_result = test.true_answers_count / test.questions.count()
    if test_result < 0.25:
        current_user.user_lvl -= 5
    elif test_result < 0.5:
        pass
    elif test_result > 0.7:
        current_user.user_lvl += 5
    elif test_result > 0.9:
        current_user.user_lvl += 10

    if current_user.user_lvl < 0:
        current_user.user_lvl = 0

    current_user.tests_results += f"{current_user.current_test_id}:{round(test_result * 100, 2)},{test.true_answers_count}/{test.questions.count()}END"
    current_user.current_test_id = None
    current_user.current_question_id = None

    current_user.complete_tests_id += f"{test_id},"
    db.session.add(current_user)
    db.session.commit()

    return show_educate_page()


@app.route('/complete_lecture<lecture_id>', methods=['POST'])
@login_required
def complete_lecture(lecture_id):
    complete_lectures_ids = [
        int(i) for i in current_user.complete_lectures_ids.split(",") if i != ""]
    if int(lecture_id) not in complete_lectures_ids:
        current_user.complete_lectures_ids += "," + str(lecture_id)
        current_user.user_lvl += 5
        db.session.commit()
    return show_lectures_page()


@app.route('/lecture<lecture_id>', methods=['POST'])
def show_lecture(lecture_id):
    lectures = db.session.query(Lecture).all()
    for i in lectures:
        if int(i.id) == int(lecture_id):
            return render_template('lecture.html', title=i.title, text=i.text, lecture_id=lecture_id)


def calc_avg_result():
    complete_tests_results = []
    for i in current_user.tests_results.split("END"):
        if i != "":
            complete_tests_results.append(float(i.split(":")[1].split(",")[0]))
    avg_result = round(sum(complete_tests_results) /
                       len(current_user.tests_results.split("END")), 2)
    return avg_result


@app.route('/profile')
@login_required
def show_profile():
    complete_lectures_ids = [
        int(i) for i in current_user.complete_lectures_ids.split(",") if i != ""]
    complete_tests_ids = [
        int(i) for i in current_user.complete_tests_ids.split(",") if i != ""]
    lectures_count = db.session.query(Lecture).count()
    tests_count = db.session.query(Test).count()
    try:
        percent = int((len(complete_lectures_ids) + len(complete_tests_ids)
                       ) / (lectures_count + tests_count) * 100)
        user_lvl = ""
        if 0 <= current_user.user_lvl <= 30:
            user_lvl = "Студент (доступна небольшая часть материалов)"
        elif 31 <= current_user.user_lvl <= 60:
            user_lvl = "Специалист (доступна большая часть материалов)"
        elif 61 <= current_user.user_lvl <= 100:
            user_lvl = "Эксперт (доступны все материалы)"
        return render_template('profile.html', name=current_user.name,
                               complete_lectures_count=len(
                                   complete_lectures_ids),
                               complete_tests_count=len(complete_tests_ids), tests_count=tests_count,
                               lectures_count=lectures_count, progress_bar_percent=percent, user_lvl=user_lvl,
                               avg_result=calc_avg_result())
    except ZeroDivisionError:
        return render_template('profile.html', name=current_user.name,
                               complete_lectures_count=len(
                                   complete_lectures_ids),
                               complete_tests_count=len(complete_tests_ids), tests_count=tests_count,
                               lectures_count=lectures_count, progress_bar_percent=0,
                               user_lvl="Студент (доступна небольшая часть материалов)", avg_result=calc_avg_result())


@app.route('/exit')
@login_required
def quit_from_profile():
    logout_user()
    return render_template('login.html')


@app.route('/archive_lecture<lecture_id>', methods=['POST'])
def show_archive_lecture(lecture_id):
    lectures = db.session.query(Lecture).all()
    for i in lectures:
        if int(i.id) == int(lecture_id):
            return render_template('archive_lecture.html', title=i.title, text=i.text, lecture_id=lecture_id)


@app.route('/archive_tests')
@login_required
def show_tests_archive_page():
    complete_tests = []
    complete_tests_results = []
    for i in current_user.tests_results.split("END"):
        if i != "":
            complete_tests_results.append(i.split(":")[1].split(",")[1])
    for count, (i, j) in enumerate(zip(current_user.complete_tests_ids.split(","), complete_tests_results)):
        if i != "" and j != "":
            temp = [db.session.query(Test).filter(
                Test.id == int(i)).first().name, j]
            complete_tests.append(temp)

    return render_template('archive_tests.html',
                           complete_tests=complete_tests)


@app.route('/archive_lectures')
@login_required
def show_lectures_archive_page():
    lectures = db.session.query(Lecture).all()
    complete_lectures_ids = [
        int(i) for i in current_user.complete_lectures_ids.split(",") if i != ""]
    return render_template('archive_lectures.html', lectures_list=lectures,
                           complete_lectures_ids=complete_lectures_ids)


@app.route('/tests', methods=['GET', 'POST'])
@login_required
def show_tests_page():
    complete_tests_id = [
        int(i) for i in current_user.complete_tests_ids.split(",") if i != ""]
    temp_tests = db.session.query(Test).filter(Test.lvl <= current_user.user_lvl)
    tests = []
    for i in temp_tests:
        if i.id not in complete_tests_id:
            tests.append(i)
    closed_tests = db.session.query(Test).filter(
        Test.lvl > current_user.user_lvl)
    need_lvl_list = []
    for i in closed_tests:
        need_lvl_list.append(abs(current_user.user_lvl - i.lvl))
    closed_tests = zip(closed_tests, need_lvl_list)
    print(closed_tests)
    return render_template('tests.html', tests=tests,
                           closed_tests=closed_tests)


@app.route("/lectures", methods=['POST'])
def show_lectures_page():
    lectures = db.session.query(Lecture).all()
    if current_user.is_authenticated:
        complete_lectures_ids = [
            int(i) for i in current_user.complete_lectures_ids.split(",") if i != ""]
        return render_template('lectures.html', lectures_list=lectures,
                               complete_lectures_ids=complete_lectures_ids)
    else:
        return render_template('lectures.html', lectures_list=lectures,
                               complete_lectures_ids=[])


@app.route("/admin")
@login_required
def show_admin_panel(message=""):
    if current_user.role == "admin":
        tests = db.session.query(Test).all()
        return render_template("admin.html", tests_list=tests, message=message)
    else:
        return index(message="Вы не авторизованы")


@app.route('/educate')
def show_educate_page():
    return render_template('educate.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    user = db.session.query(User).filter(User.username == username).first()
    if user and user.check_password(password):
        login_user(user, remember=True)
        return show_profile()
    else:
        return render_template("login.html", message="Ошибка авторизации")


if __name__ == '__main__':
    app.app_context().push()
    db.create_all()
    app.run()
