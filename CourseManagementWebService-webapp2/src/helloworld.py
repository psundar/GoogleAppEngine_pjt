#from google.appengine.ext import webapp
#[START imports]
import webapp2
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from modelHandlers import departmentHandler, studentHandler
from modelHandlers import courseHandler, scheduleHandler, enrollmentsHandler
from google.appengine.ext.key_range import ndb
#[END imports]

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.response.out.write(template.render('main.html',{}))
            #self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('Hello, '+user.nickname())
        
    def post(self):
        self.response.out.write('posted!')

   
''' Using toplevel makes sure that all asynchronous put requests have been handled before handler exits'''
application = ndb.toplevel(webapp2.WSGIApplication([
                webapp2.Route(r'/', handler=MainPage, name='Main'),
                webapp2.Route(r'/department', handler=departmentHandler, name='department'),
                webapp2.Route(r'/course', handler=courseHandler, name='course'),
                webapp2.Route(r'/student', handler=studentHandler, name='student'),
                webapp2.Route(r'/schedule', handler=scheduleHandler, name='schedule' ),
                webapp2.Route(r'/enrollments', handler=enrollmentsHandler, name='enrollments')
                ], debug=True))


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
