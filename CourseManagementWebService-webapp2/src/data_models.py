'''
Created on Sept, 2016

@author: pratibha
'''
#[START imports]
from google.appengine.ext.key_range import ndb
from protorpc import messages

#[END imports]
'''
 A basic NDB based data models module
'''
 
class Department(ndb.Model):
    
    department_id = ndb.IntegerProperty()
    name = ndb.StringProperty()

class Course(ndb.Model):
    '''
    Course Object
    '''
    "Eg: 14531, 09864"
    course_id = ndb.IntegerProperty()
    name = ndb.StringProperty()
    department = ndb.KeyProperty(kind=Department)
    instructor = ndb.StringProperty()
    # values are time ranges. E.g: "9:30am - noon" Since this is going to be only for viewing and not processing, string will suffice.
    time = ndb.StringProperty()
    place = ndb.StringProperty()

class coursesMessage(messages.Message):
    ''' contains list of courses a student is enrolled in. Contents of Student.study_lists'''
    courses = messages.StringField(1, repeated = True)
 
class Student(ndb.Model):
    '''
    Student Object
    '''
    # Ideally a student ID is best a String and not a number and it can be a combination of dept,batch and rollno. 
    #For simplicity, it is set an integer.
    # Implicitly setting this varibale as the key
    student_id = ndb.IntegerProperty()
    name = ndb.StringProperty()
    address = ndb.StringProperty()
    phone_number = ndb.IntegerProperty()
    # Parent - Child relationship to retrieve department name
    department = ndb.KeyProperty(kind=Department)
    #department_name = ndb.KeyProperty(kind = Department)
    # similar to an array. study list can be list of things to study for a student
    study_lists = ndb.KeyProperty(kind = Course, repeated = True)
        
class studentsMessage(messages.Message):
    students = messages.StringField(1, repeated=True)

class Schedule(ndb.Model):
    '''
    Course Schedule by Quarter Module
    '''
    " Quarter can be, 1, 2 "
    #schedule_id = ndb.FloatProperty()
    year = ndb.IntegerProperty()
    quarter = ndb.IntegerProperty()
    department = ndb.KeyProperty(kind=Department)
    course = ndb.KeyProperty(kind=Course)
    
class Enrollment(ndb.Model):
    '''
    Student Enrollment for a given quarter View
    '''
    student = ndb.KeyProperty(kind=Student)
    schedule = ndb.KeyProperty(kind=Schedule)
    
    
        