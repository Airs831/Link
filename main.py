import webapp2
import logging
import jinja2
import os
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import search
from urlparse import urlparse

from datetime import date


jinja_env = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__))
)

class Profile(ndb.Model):
    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    email = ndb.StringProperty()
    dates_free = ndb.StringProperty(repeated=True)
    friends = ndb.KeyProperty(repeated=True, kind='Profile')

def parseDate(inputString):
    split_string = inputString.split('-')
    index = [1,2,0]
    temp = [split_string[x] for x in index]
    perm = '-'.join(temp)
    return perm

# def check_month(month):
#     switcher={
#                 01:'January',
#                 02:'February',
#                 03:'March',
#                 04:'April',
#                 05:'May',
#                 06:'June'
#                 07:'July',
#                 08:'August',
#                 09:'September',
#                 10:'October',
#                 11:'November',
#                 12:'December',
#              }
#     return switcher.get(month,"Invalid Month")

# def check_month(x):
#     return {
#          01:'January',
#          02:'February',
#          03:'March',
#          04:'April',
#          05:'May',
#          06:'June',
#          07:'July',
#
#     }.get(x, "not a month")

def get_current_email():
    return users.get_current_user()

def get_current_profile():
    current_user = get_current_email()
    return Profile.query().filter(current_user.email() == Profile.email).get()

def get_all_profiles():
    return Profile.query().fetch()

class Login(webapp2.RequestHandler):
    def get(self):
        login_url = users.create_login_url('/')
        template_vars = {
            "login_url": login_url
        }
        template = jinja_env.get_template('templates/login.html')
        self.response.write(template.render(template_vars))
    def post(self):
        self.redirect("/")

class Home(webapp2.RequestHandler):
    def get(self):
        current_user = get_current_email()
        all_people = get_all_profiles()

        if current_user:
            email_address = current_user.email()
            logout_link = users.create_logout_url('/login')
            is_existing_person = False
            for person in all_people:
                if person.email == email_address:
                    is_existing_person = True

            if (is_existing_person == False):
                new_user = Profile(
                    email=current_user.email(),
                    friends = [],
                    dates_free = [],
                )
                new_user.put()
                template = jinja_env.get_template('templates/registration.html')
                self.response.write(template.render())

            else:
                user_free_dates = sorted(get_current_profile().dates_free)
                friend_list = get_current_profile().friends
                first_name = get_current_profile().first_name
                template_vars = {
                    "first_name": first_name,
                    "user_free_dates": user_free_dates,
                    "logout_link": logout_link,
                    "friend_list": friend_list
                }
                template = jinja_env.get_template('templates/home.html')
                self.response.write(template.render(template_vars))

        else:
            self.redirect("/login")

    def post(self):
        current_user = get_current_email()
        get_current_user = get_current_profile()
        first_name = self.request.get("first_name")
        last_name = self.request.get("last_name")
        get_current_user.first_name = first_name
        get_current_user.last_name = last_name
        get_current_user.put()
        self.redirect('/')

class EditProfile(webapp2.RequestHandler):
    def get(self):
        current_user = users.get_current_user()
        get_current_user = get_current_profile()
        added_dates = sorted(get_current_user.dates_free)
        for date in added_dates:
            parse_dates = []
            parse_dates.append(parseDate(date))
        if get_current_user.dates_free:
            template_vars = {
                'current_user': current_user,
                'added_dates': added_dates,
                'currentDate': currentDate,
                'parse_dates': parse_dates
            }
        else:
            template_vars = {
            'current_user': current_user,
            'added_dates': added_dates,
            }
        template = jinja_env.get_template('templates/profile.html')
        self.response.write(template.render(template_vars))
    def post(self):
        current_user = users.get_current_user()
        get_current_user = get_current_profile()
        user_free_date = self.request.get('user_free_date')

        #Only add date if not already added
        if user_free_date not in get_current_user.dates_free:
            get_current_user.dates_free.append(user_free_date)

        get_current_user.put()
        self.redirect("/profile")

        template_vars = {
            'date': user_free_date,
        }
        template = jinja_env.get_template('templates/profile.html')
        self.response.write(template.render(template_vars))

class Friends(webapp2.RequestHandler):
    def get(self):
        current_user = users.get_current_user()
        get_current_user = get_current_profile()
        all_users = Profile.query().filter(current_user.email() != Profile.email).fetch()
        # filtered_users = all_users.filter(Profile.email != Profile.friends.email).fetch()
        template_vars = {
            "all_users": all_users,
            'get_current_user': get_current_user
        }
        template = jinja_env.get_template('templates/friends.html')
        self.response.write(template.render(template_vars))
    def post(self):
        current_user = get_current_email()
        get_current_user = get_current_profile()
        all_people = get_all_profiles()
        search = self.request.get('search')
        searched_friends = Profile.query().filter(Profile.first_name == search).fetch()
        print searched_friends

        for person in all_people:
            if_checked_person = self.request.get(person.email)
            if if_checked_person == "on":
                get_current_user.friends.append(person.key)
                get_current_user.put()
        template_vars = {
            "searched_friends": searched_friends,
        }
        template = jinja_env.get_template('templates/friends.html')
        self.response.write(template.render(template_vars))
class Schedule(webapp2.RequestHandler):
    def get(self):
        template_vars = {
        }
        template = jinja_env.get_template('templates/schedule.html')
        self.response.write(template.render(template_vars))

    def post(self):
        current_user = get_current_email()
        get_current_user=get_current_profile()
        hangout_date = self.request.get("hangout_date")
        friends_free = []
        if len(get_current_user.friends) != 0:
            for friend in get_current_user.friends:
                if len(friend.get().dates_free) != 0:
                    for date in friend.get().dates_free:
                        if hangout_date == date:
                            friends_free.append(friend.get().first_name)

        template_vars = {
            "hangout_date": hangout_date,
            "get_current_user": get_current_user,
            "friends_free": friends_free
        }
        template = jinja_env.get_template('templates/linkup.html')
        self.response.write(template.render(template_vars))

class populateDatabase(webapp2.RequestHandler):
    def get(self):
        alexa = Profile(
            first_name = 'Alexa',
            last_name = 'Ramirez',
            email = 'alexa@gmail.com',
            dates_free = ["2019-11-30", "2019-10-11",],
            friends = []
        )
        alexa_key = alexa.put()

        ashlee = Profile(
            first_name = 'Ashlee',
            last_name = 'Kupor',
            email = 'ashlee@example.com',
            dates_free = ["2019-11-30", "2019-12-11",],
            friends = []
        )
        ashlee_key = ashlee.put()

        alexa.friends = [ashlee_key]
        ashlee.friends = [alexa_key]

        alexa_key = alexa.put()
        ashlee_key = ashlee.put()

        self.redirect("/")

app=webapp2.WSGIApplication([
    ('/login', Login),
    ('/', Home),
    ('/profile', EditProfile),
    ('/friends', Friends),
    ('/schedule', Schedule),
    ('/populateDatabase', populateDatabase),
], debug=True)
