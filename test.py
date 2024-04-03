from flask import Flask, render_template, redirect, request, url_for
from wtforms import SelectField, SubmitField, StringField, IntegerField, validators, TextAreaField, FieldList, \
    BooleanField, RadioField
from flask_wtf import FlaskForm
import os
from catboost import CatBoostRegressor
import requests

from wtforms.validators import DataRequired

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
model = CatBoostRegressor()
dd = {}
model.load_model("good.cbm")


def get_coordinates(address):
    api_key = "40d1649f-0493-4b70-98ba-98533de7710b"
    url = 'https://geocode-maps.yandex.ru/1.x/'
    params = {
        'apikey': api_key,
        'geocode': address,
        'format': 'json'
    }

    response = requests.get(url, params=params)
    data = response.json()

    try:
        coordinates_str = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        longitude, latitude = map(float, coordinates_str.split())
        return latitude, longitude
    except (KeyError, IndexError, ValueError):
        return None


homes = {"Другое": 0, "Панельный": 1, "Монолитный": 2, "Кирпичный": 3, "Блочный": 4, "Деревянный": 5}
rooms = {"Студия": -1, "1 комната": 1, "2 комнаты": 2, "3 комнаты": 3, "4 комнаты": 4, "5+ комнат": 5}

object_type = {"Вторичка": 1, "Новойстройка": 2}


@app.route("/")
def asd():
    class Start(FlaskForm):
        submit_start = SubmitField("Начать")

    form = Start()

    return render_template("main_window.html", form=form)


@app.route('/start', methods=['POST', 'GET'])
def start():
    global dd

    class Reg_home(FlaskForm):
        nedv = SelectField(choices=[("Квартира", "Квартира"), ("Дом", "Дом"), ("Участок", "Участок"), ("ЖК", "ЖК")])
        address = StringField(render_kw={"placeholder": "Адрес"}, validators=[DataRequired()])
        area = IntegerField('Площадь в м²', render_kw={"placeholder": "Площадь в м²"},
                            validators=[validators.NumberRange(min=0, max=999), DataRequired()])
        living_area = IntegerField('Жилая площадь в м²', render_kw={"placeholder": "Жилая площадь в м²"},
                                   validators=[validators.NumberRange(min=0, max=999)])
        kitchen_area = IntegerField('Площадь кухни в м²', render_kw={"placeholder": "Площадь кухни в м²"},
                                    validators=[validators.NumberRange(min=0, max=999)])
        rooms = SelectField(choices=[("Студия", "Студия"), ("1 комната", "1 комната"),
                                     ("2 комнаты", "2 комнаты"), ("3 комнаты", "3 комнаты"), ("4 комнаты", "4 комнаты"),
                                     ("5+ комнат", "5+ комнат")])

        submit_start = SubmitField("Оценить")

        def __init__(self, chosen_nedv="", chosen_rooms="", chosen_area="", chosen_living_area="", chosen_address="",
                     chosen_kitchen_area="",
                     *args, **kwargs):
            super(Reg_home, self).__init__(*args, **kwargs)
            if not self.submit_start.data:
                if chosen_nedv != "":
                    self.nedv.data = chosen_nedv
                if chosen_area != "":
                    self.area.data = chosen_area
                if chosen_rooms != "":
                    self.rooms.data = chosen_rooms
                if chosen_address != "":
                    self.address.data = chosen_address
                if chosen_living_area != "":
                    self.living_area.data = chosen_living_area
                if chosen_kitchen_area != "":
                    self.kitchen_area.data = chosen_kitchen_area

    try:
        nedv = dd["Дом/квартира"]
    except:
        nedv = ""
    try:
        rooms = dd["Колво комнат"]
    except:
        rooms = ""
    try:
        area = dd["Площадь"]
    except:
        area = ""
    try:
        address = dd["Адрес"]
    except:
        address = ""
    try:
        living_area = dd["Жилая площадь"]
    except:
        living_area = ""

    try:
        kitchen_area = dd["Площадь кухни"]
    except:
        kitchen_area = ""
    form = Reg_home(nedv, rooms, area, living_area, address, kitchen_area)

    if form.submit_start.data:
        address = form.address.data
        coordinat = get_coordinates(address)
        dd["Широта"] = coordinat[0]
        dd["Долгота"] = coordinat[1]

        dd["Колво комнат"] = form.rooms.data
        dd["Адрес"] = form.address.data
        dd["Площадь"] = form.area.data
        dd["Дом/квартира"] = form.nedv.data
        dd["Жилая площадь"] = form.living_area.data
        dd["Площадь кухни"] = form.kitchen_area.data

        return redirect('/type_home')
    return render_template('begin.html', form=form)


@app.route('/type_home', methods=['POST', 'GET'])
def type_home():
    class TypeHomeForm(FlaskForm):
        choices = RadioField(choices=[("Другое", "Другое"), ('Кирпичный', "Кирпичный"), ("Панельный", "Панельный"),
                                      ("Деревянный", "Деревянный"), ("Монолитный", "Монолитный"),
                                      ("Блочный", "Блочный")], validators=[DataRequired()])
        back = SubmitField("Назад")
        submit = SubmitField("Дальше")

        def __init__(self, ch_floors, *args, **kwargs):
            super(TypeHomeForm, self).__init__(*args, **kwargs)
            if not self.back.data and not self.submit.data:
                if ch_floors != "":
                    self.choices.data = ch_floors

    try:
        ind = dd["Тип дома"].lower().capitalize()
    except:
        ind = ""

    form = TypeHomeForm(ind)

    if form.submit.data:
        dd["Тип дома"] = form.choices.data
        return redirect('/floors')
    if form.back.data:
        dd["Тип дома"] = form.choices.data
        return redirect("/start")
    if ind != "":
        print(ind)
        return render_template('type_home.html', form=form, zvzv=ind)
    return render_template('type_home.html', form=form)


@app.route("/floors", methods=["POST", "GET"])
def floors():
    class Floors(FlaskForm):
        floors = IntegerField(render_kw={"placeholder": "Количество этажей"},
                              validators=[validators.NumberRange(1, 100)])
        back_fl = SubmitField("Назад")
        submit_fl = SubmitField("Дальше")

        def __init__(self, ch_floors, *args, **kwargs):
            super(Floors, self).__init__(*args, **kwargs)
            if not self.back_fl.data and not self.submit_fl.data:
                if ch_floors != "":
                    self.floors.data = ch_floors

    global dd
    try:
        floors = dd["Колво этажей"]
    except:
        floors = ""
    form = Floors(floors)
    if form.back_fl.data:
        dd['Колво этажей'] = form.floors.data
        return redirect('/type_home')

    if form.submit_fl.data:
        dd["Колво этажей"] = form.floors.data
        return redirect('/now_floor')
    return render_template("floors.html", form=form)


@app.route("/now_floor", methods=["POST", "GET"])
def now_floor():
    class Now_floor(FlaskForm):
        floors = IntegerField(render_kw={"placeholder": "Этаж квартиры"},
                              validators=[validators.NumberRange(1, 100)])
        back_now = SubmitField("Назад")
        submit_now = SubmitField("Дальше")

        def __init__(self, ch_floors, *args, **kwargs):
            super(Now_floor, self).__init__(*args, **kwargs)
            if not self.back_now.data and not self.submit_now.data:
                if ch_floors != "":
                    self.floors.data = ch_floors

    global dd
    try:
        now_floor = dd["Нынешний этаж"]
    except:
        now_floor = ""

    form = Now_floor(now_floor)
    if form.back_now.data:
        dd["Нынешний этаж"] = form.floors.data
        return redirect('/floors')

    if form.submit_now.data:
        dd["Нынешний этаж"] = form.floors.data
        return redirect('/total')
    return render_template("now_floor.html", form=form)


def get_price(dd):
    global rooms, homes, model
    try:
        geo_lat = dd["Широта"]
    except:
        geo_lat = None
    try:
        geo_lon = dd["Долгота"]
    except:
        geo_lon = None
    try:
        home = homes[dd["Тип дома"]]
    except:
        home = None
    stage = dd["Нынешний этаж"]
    levels = dd["Колво этажей"]

    try:
        komnati = rooms[dd["Колво комнат"]]
    except:
        komnati = None
    area = float(dd["Площадь"])

    kitchen_area = float(dd["Площадь кухни"])

    lst = [[geo_lat, geo_lon, 1, home, stage, levels, komnati, area, kitchen_area, 1]]
    print(lst)
    kk = model.predict(lst)
    return int(kk)


@app.route("/total", methods=["POST", "GET"])
def total():
    class Back(FlaskForm):
        back_total = SubmitField("Назад")

    form = Back()
    if form.back_total.data:
        return redirect("/now_floor")

    price = get_price(dd)
    return render_template("total.html", form=form, price=price)


if __name__ == '__main__':
    app.run()
