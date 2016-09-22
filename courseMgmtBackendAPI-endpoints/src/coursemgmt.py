# [START imports]
import endpoints
#from protorpc import message_types
from protorpc import messages
from protorpc import remote


from data_models import Student
from data_models import Department
from data_models import Course
from data_models import Schedule
from data_models import Enrollment
from data_models import coursesMessage
from data_models import studentsMessage

from google.appengine.ext import ndb

# [END imports]

'''
1. Functional requirements
a. Allows user to add /edit/remove student information:
    i. Student Id, name, department, address, phone number, study list, etc.
b. Allows user to add/edit/remove course information:
    i. Course id, department, name, instructor, time, place, etc.
c. Allows user to add/edit/remove course schedule:
    i. Quarter, department, courses provided in the quarter, etc.
d. Allows user to enroll/drop a student to/from a course
e. Allows user to list students enrolled in a course
f. Allows user to list courses a student enrolls in
g. Allows user to list courses a department provides in a specific quarter

Assumptions:
1. All id fields are integers
'''
#[START messages]
class responseMsg(messages.Message):
    ''' Object to store response message to be sent to client'''
    message = messages.StringField(1)   

class responseCollection(messages.Message):
    '''Collection of response messages'''
    items = messages.MessageField(responseMsg, 1, repeated=True)

STORED_RESPONSES = responseCollection(items=[
    responseMsg(message='New Record inserted successfully!'),
    responseMsg(message='Data deleted successfully!'),
    responseMsg(message='Enrolled a student successfully'),
    responseMsg(message='Dropped a student successfully'),
    responseMsg(message= 'Insert Error: Unable to insert. Record already exists. Try Update!'),
    responseMsg(message= 'Reference Key Not Found Error: Invalid Department ID. Check for valid ID from department data.'),
    responseMsg(message='Reference Key Not Found Error: Invalid Course ID. Check for valid ID from course.'),
    responseMsg(message='Reference Key Not Found Error: Invalid Student ID. Check for valid ID from student.'),
    responseMsg(message='Reference Key Not Found Error: Schedule not found. Please check schedules for valid course, quarter, department and year'),
    responseMsg(message='Entity Not Found. Check datastore for valid entry'),
    responseMsg(message='Dependency Error: Enrollments found for student. Delete Enrollments before deleting student'),
    responseMsg(message='Dependency Error: Course found in Schedule. Delete Course from Schedule(automatically deletes from Student and Enrollments).'),
    responseMsg(message='Dependency Error: Department found in Student entities. Make sure dept. not found in Student/Course/Schedule before deleting'),
    responseMsg(message='Dependency Error: Department found in Course entities. Make sure dept. not found in Student/Course/Schedule before deleting'),
    responseMsg(message='Dependency Error: Department found in Schedule entities. Make sure dept. not found in Student/Course/Schedule before deleting')
     ])

#STORED_ERRORS = ['Insert Error: Unable to insert. Record already exists. Try Update!',
#                 'Reference Key Not Found Error: Invalid Department ID. Check for valid ID from department data.']

'''
TO-DOs
STORE constants in Enum??
'''

# Success Responses
ADD_ID = 0
DELETE_ID = 1
ENROLL_ID = 2
DROP_ID = 3
# Error Responses
DUPLICATE_ID = 4
INV_DEPT_ID = 5
INV_COURSE_ID = 6
INV_STUDENT_ID = 7
INV_SCHEDULE_ID = 8
NOT_FOUND_ID = 9
DEP_ERR_STUDENT_ID = 10
DEP_ERR_COURSE_ID = 11
DEP_ERR_DEPT_ST_ID = 12
DEP_ERR_DEPT_CO_ID = 13
DEP_ERR_DEPT_SCH_ID = 14
#[END messages]


#[START Resource Container]
# ResourceContainers are used to encapsuate a request body and url
    # parameters.
'''    
1. Department Containers for Add/Delete/View
'''
#VIEW_DEPARTMENT_CONTAINER = endpoints.ResourceContainer(
 #       id = messages.IntegerField(1, variant=messages.Variant.INT64))

ADD_DEPARTMENT_CONTAINER = endpoints.ResourceContainer(
        id = messages.IntegerField(1, variant=messages.Variant.INT64),
        name = messages.StringField(2))

REMOVE_DEPARTMENT_CONTAINER = endpoints.ResourceContainer(
        id = messages.IntegerField(1, variant=messages.Variant.INT64)) 
'''
2. Course Container
Functional Requirement:
b. Allows user to add/edit/remove course information:
    i. Course id, department, name, instructor, time, place, etc.
'''
#VIEW_COURSE_CONTAINER = endpoints.ResourceContainer(
 #       id =messages.IntegerField(1, variant=messages.Variant.INT64) )

ADD_COURSE_CONTAINER = endpoints.ResourceContainer(
        id = messages.IntegerField(1, variant=messages.Variant.INT64),
        name = messages.StringField(2),
        department_id = messages.IntegerField(3, variant=messages.Variant.INT64),
        instructor = messages.StringField(4),
        time = messages.StringField(5),
        place = messages.StringField(6))

REMOVE_COURSE_CONTAINER = endpoints.ResourceContainer(
        id = messages.IntegerField(1))   

'''       
3. Student Container
Functional Requirement:
a. Allows user to add /edit/remove student information:
    i. Student Id, name, department, address, phone number, study list, etc.
'''    
#VIEW_STUDENT_CONTAINER = endpoints.ResourceContainer(
 #       id = messages.IntegerField(1, variant=messages.Variant.INT64) )
                      
ADD_STUDENT_CONTAINER = endpoints.ResourceContainer(
        id = messages.IntegerField(1, variant=messages.Variant.INT64),
        name = messages.StringField(2),
        department_id = messages.IntegerField(3, variant=messages.Variant.INT64),
        address = messages.StringField(4),
        phone_number = messages.IntegerField(5, variant=messages.Variant.INT64))

REMOVE_STUDENT_CONTAINER = endpoints.ResourceContainer(
        id = messages.IntegerField(1, variant=messages.Variant.INT64))

'''
Functional Requirement:
f. Allows user to list courses a student enrolls in
'''
# uses only student model
VIEW_STUDENT_COURSES_CONTAINER = endpoints.ResourceContainer(
        student_id = messages.IntegerField(1, variant=messages.Variant.INT64))

# NOTE: added one more property called schedule id. check to see if id itself is suffice

'''
4. Schedule Container
Functional Requirement:
g. Allows user to list courses a department provides in a specific quarter
'''
# uses schedule model
VIEW_DEPT_COURSES_CONTAINER = endpoints.ResourceContainer(
        department_id = messages.IntegerField(1, variant=messages.Variant.INT64),
        quarter = messages.IntegerField(2, variant=messages.Variant.INT64),
        year = messages.IntegerField(3, variant=messages.Variant.INT64))

ADD_SCHEDULE_CONTAINER = endpoints.ResourceContainer(
        year = messages.IntegerField(1, variant=messages.Variant.INT64),
        quarter = messages.IntegerField(2, variant=messages.Variant.INT64),
        #department_id = messages.IntegerField(3, variant=messages.Variant.INT64),
        course_id = messages.IntegerField(3, variant=messages.Variant.INT64)
        )

REMOVE_SCHEDULE_CONTAINER = endpoints.ResourceContainer(
        year = messages.IntegerField(1, variant=messages.Variant.INT64),
        quarter = messages.IntegerField(2, variant=messages.Variant.INT64),
        #department = messages.IntegerField(3, variant=messages.Variant.INT64),
        course_id = messages.IntegerField(3, variant=messages.Variant.INT64)
        )
'''
5. Enrollments Container
Functional Requirement:
e. Allows user to list students enrolled in a course
'''
# uses both schedule and Enrollment models
VIEW_COURSE_STUDENTS_CONTAINER = endpoints.ResourceContainer(
        course_id = messages.IntegerField(1, variant=messages.Variant.INT64))
        #department_id = messages.IntegerField(2, variant=messages.Variant.INT64))

'''
Functional Requirement:
c. Allows user to add/edit/remove course schedule:
    i. Quarter, department, courses provided in the quarter, etc.
'''
ADD_ENROLLMENTS_CONTAINER = endpoints.ResourceContainer(
        student_id = messages.IntegerField(1, variant=messages.Variant.INT64),
        course_id = messages.IntegerField(2, variant=messages.Variant.INT64),
        #department_id = messages.IntegerField(3, variant=messages.Variant.INT64),
        quarter = messages.IntegerField(4, variant=messages.Variant.INT64),
        year = messages.IntegerField(5, variant=messages.Variant.INT64)
        )

DELETE_ENROLLMENTS_CONTAINER = endpoints.ResourceContainer(
        student_id = messages.IntegerField(1, variant=messages.Variant.INT64),
        course_id = messages.IntegerField(2, variant=messages.Variant.INT64),
        #department_id = messages.IntegerField(3, variant=messages.Variant.INT64),
        quarter = messages.IntegerField(4, variant=messages.Variant.INT64),
        year = messages.IntegerField(5, variant=messages.Variant.INT64))
#[END Resource Container]



#[START api]

# 1. Department Api
@endpoints.api(name='department', version='v1')
class DepartmentApi(remote.Service):
    '''
    Api for Department Model to do operations like add/edit/view
    '''
    '''
    TO_DOs
    1. Enforce constraints for ID. E.g. Length, range 
    2. Check whether name case sensitivity matters?
    '''
    
    def upsertDepartment(self, request, message_ID):
        ''' Method to create/update a department entity'''
        department = Department(id=request.id, department_id=request.id, name=request.name)
        print("New department Key = ",department.put())
        return STORED_RESPONSES.items[message_ID]
    
    def getDepartment(self, dept_id):
        d_key = ndb.Key(Department, dept_id)
        return d_key.get()
    '''OK'''
    # Endpoint method to add department entities
    @endpoints.method(ADD_DEPARTMENT_CONTAINER, responseMsg,
                      path='department/add', http_method='GET', name='department.add')
    def insertDept(self, request):
        try:
            ''' insert new department given department ID'''
            # Checking if the record exists already
            department = self.getDepartment(request.id) 
            if not department:
                # New record
                print "New Department to be added"
                response = self.upsertDepartment(request, ADD_ID)
            else:
                # Record exists. Cannot insert. Need to update. Send Error message back
                response =  STORED_RESPONSES.items[DUPLICATE_ID]
            return response
                
        except:
            raise endpoints.EndpointsErrorMessage(
                'Unable to add department record. Please try again later.')
            
     
    # endpoint method to update department records
     
            
    '''OK'''
    # endpoint method to delete a department entity
    @endpoints.method(REMOVE_DEPARTMENT_CONTAINER, responseMsg,
                      path='department/delete', http_method='GET', name='department.delete')
    def deleteDept(self, request):
        ''' delete department given department ID. delete in the order Schedule, Student and Course first'''
        # Enhancement. Deleting entity using other details like department name
        try:
            # Creating the key for given department id
            d_key = ndb.Key(Department, int(request.id))
            # Fetching and deleting the entity
            dept = Department.get_by_id(request.id)
            ''' Dependencies'''
            # check if department exists in Student kind
            st_query = Student.query(Student.department == d_key)
            co_query = Course.query(Course.department == d_key)
            sch_query = Schedule.query(Schedule.department == d_key)
            if sch_query.get():
                # entity found in Schedule. Invoke Dependency error
                response = STORED_RESPONSES.items[DEP_ERR_DEPT_SCH_ID]
            elif st_query.get():
                # entity found in Student. Invoke Dependency error
                response = STORED_RESPONSES.items[DEP_ERR_DEPT_ST_ID]
            elif co_query.get():
                # entity found in Course. Invoke Dependency error
                response = STORED_RESPONSES.items[DEP_ERR_DEPT_CO_ID]
            else:
                # no dependencies found. delete department
                print("Department to be deleted = ", dept)
                d_key.delete()
                response = STORED_RESPONSES.items[DELETE_ID]
            return response
        
        except:
            raise endpoints.EndpointsErrorMessage("Unable to delete entity. Please try again later!")
            
# 2. Course Api
@endpoints.api(name='course', version='v1')
class CourseApi(remote.Service):
    '''
    Api for all operations like add/edit/view on the Course Model
    '''
    '''
    TO-DOs
    1. Validate time to see if it is of specified format "9:00 am to 12:00 pm"
    2. Referential constraints on department 
    3. Datetime for time?
    
    Assumptions:
    1. Course ID needs to be unique across all departments
    '''
    def getCourse(self, course_id):
        ''' return course entity given ID'''
        c_key = ndb.Key(Course, course_id)
        return c_key.get()
    
    def getDepartment(self, dept_id):
        ''' Get department entity given department ID'''
        dept_key = ndb.Key(Department, dept_id)
        return dept_key.get()    
    
    def upsertCourse(self, request, message_ID):
        ''' insert or update course entity'''
        course = Course(id=request.id, course_id=request.id, name = request.name, department = ndb.Key(Department, request.department_id) , 
                                    instructor=request.instructor, time = request.time, place=request.place)
                    
        course.put()
        return STORED_RESPONSES.items[message_ID]
        
    # endpoint method to add a course
    @endpoints.method(ADD_COURSE_CONTAINER, responseMsg,
                      path='course/add', http_method='GET', name='course.add')
    def insertCourse(self, request):
        ''' insert a new course given course ID and department ID. course ID is unique across depts.'''
        try:
            response = ""
            
            course = self.getCourse(request.id)
            # check for valid department
            department = self.getDepartment(request.department_id)
            # Course Not found. Insert new course
            if not course:
                # Validate department
                if department:
                    # create new course 
                    response = self.upsertCourse(request, ADD_ID)
                else:
                    response = STORED_RESPONSES.items[INV_DEPT_ID]
            else:
                # Course found. cannot insert but update 
                response = STORED_RESPONSES.items[DUPLICATE_ID] 
            return response 
        except:
            raise endpoints.EndpointsErrorMessage(
                'Unable to add course record. Please try again later. ')
    
    '''OK'''
    ''' TO-Dos
    1. When course is deleted, schedule, enrollment and student.study_lists to be deleted
    '''
    # endpoint method to delete a course
    @endpoints.method(REMOVE_COURSE_CONTAINER, responseMsg,
                      path='course/delete', http_method='GET', name='course.delete')
    def deleteCourse(self, request):
        '''Delete a course given course ID. Delete course from Schedule first.'''
        try:
            response = ""
            # Creating the key for given course id
            c_key = ndb.Key(Course, request.id)
            # Check if course exists
            if c_key.get():
                '''Dependency Check'''
                # Check if course exists in schedule
                query = Schedule.query(Schedule.course == c_key)
                if query.get():
                    # course exists in schedule. Invoke dependency error
                    response = STORED_RESPONSES.items[DEP_ERR_COURSE_ID]
                else: 
                    # Fetching and deleting the entity with given course_id 
                    c_key.delete()
                    response = STORED_RESPONSES.items[DELETE_ID]
            return response 
        except:
            raise endpoints.EndpointsErrorMessage(
                'Unable to delete course entity. Please try again later. ')
 
# 3. Student Api    
@endpoints.api(name='student', version='v1')
class StudentApi(remote.Service):
    '''
    Api for all operations like add/edit/view on the Student Model
    '''
    ''' TO-DOs
    1. Add Ref constraints w.r.t department and list of courses
    2. Make study lists as collection of course_ids. Check Structured Entity
    http://stackoverflow.com/questions/14072491/app-engine-structured-property-vs-reference-property-for-one-to-many-relationsh
    3. Validate length of student ID
    4. Validate length of phone number
    
    Assumption:
    Study lists will only get populated when a student is enrolled in a course through the enrollment api
    '''
    def getStudent(self, student_id):
        ''' get student entity given ID'''
        s_key = ndb.Key(Student, student_id)
        return s_key.get()
    
    def getDepartment(self, dept_id):
        ''' get department entity given department ID'''
        dept_key = ndb.Key(Department, dept_id)
        return dept_key.get()
    
    def upsertStudent(self, request, message_ID):
        ''' insert or update Student entity'''
        student = Student(id=request.id, student_id=request.id, name=request.name, 
                          address=request.address, phone_number=request.phone_number, 
                          department=ndb.Key(Department, request.department_id))
        print("Inserting a new record into the datastore",student.put())
        return STORED_RESPONSES.items[message_ID]                        
    
    '''OK'''
    # endpoint method to add a student entity
    @endpoints.method(ADD_STUDENT_CONTAINER, responseMsg,
        path='student/add', http_method='GET', name='student.add')
    def insertStudent(self, request):
        ''' Insert student entity given student ID'''
        try:
            response = ""
            # Check if student id already exists
            student = self.getStudent(request.id)
            if not student:
                # Check if department is valid 
                dept = self.getDepartment(request.department_id) 
                if(not dept):
                    # Invalid department id
                    print("Department record not found!", dept)
                    response = STORED_RESPONSES.items[INV_DEPT_ID]
                else:
                    print("New student record to be added",student)   
                    # insert student entity
                    response = self.upsertStudent(request, ADD_ID)
                
            else:
                #Send Error Message
                response = STORED_RESPONSES.items[DUPLICATE_ID] 
            return response
        except:
            raise endpoints.EndpointsErrorMessage(
                'Unable to add student entity. Please try again later. ')
    '''OK'''
    '''
    To-Dos
    1. When student is deleted, enrollment is deleted
    '''
    # endpoint method to delete a student
    @endpoints.method(REMOVE_STUDENT_CONTAINER, responseMsg,
                      path = 'student/delete', http_method='GET', name='student.delete')
    def deleteStudent(self, request):
        ''' Delete student entity given student id'''
        try:
            response = ""
            # Create a key for given student id
            s_key = ndb.Key(Student, int(request.id))
            student = Student.get_by_id(request.id)
            print("Key generated for student = ", s_key, student)
            # Fetching student entity
            #student = Student.get_by_id(s_key)
            #student = s_key.get()
            #print ("Student Record to be deleted = ", student)
            
            if student:
                # check if the student is enrolled in a course or not. 
                query = Enrollment.query(Enrollment.student == s_key)
                if query.get():
                    # cannot delete student without deleting his enrollments
                    response = STORED_RESPONSES.items[DEP_ERR_STUDENT_ID]
                else:
                    # deleting the entity with a given student id
                    s_key.delete()
                    response = STORED_RESPONSES.items[DELETE_ID]
            else:
                response = STORED_RESPONSES.items[INV_STUDENT_ID]
            
            return response
        except:
            raise endpoints.EndpointsErrorMessage(
                    'Unable to delete student entity. Please try again later.')
     
    def copyToCoursesMessage(self, study_lists):
        print("Inside copyToCourseMessage method")
        cm = coursesMessage()
        for c in study_lists:
            cm.courses.append(c.get().name)
        print("copyToCoursesMessage method: courses =", cm)
        return cm
     
    ''' Functional Requirement: 
    f. Allows user to list courses a student enrolls in'''       
    @endpoints.method(VIEW_STUDENT_COURSES_CONTAINER, coursesMessage, 
                      path='student/coursesByStudent', http_method='POST', name= 'student.coursesByStudent')
    def view_courses_by_student(self, request):
        ''' List courses a student enrolls in'''
        # Validate student id
        s_key = ndb.Key(Student, request.student_id)
        study_lists = None
        if s_key:
            study_lists = s_key.get().study_lists
            # access structured property, form messages and return them
        print("Inside view_courses_by_student method")
        return self.copyToCoursesMessage(study_lists)
    
# 4. Schedule Api
@endpoints.api(name='schedule', version='v1')
class ScheduleApi(remote.Service):
    '''
    Api for all scheduling operations like add/drop courses, view schedules
    '''
    '''
    TO-DOs
    1. Validate year
    2. Validate Quarter. Use fixed value.
    '''
    
    def upsertSchedule(self, request, d_key, message_ID):
        ''' insert or update Schedule entity'''
        schedule = Schedule(year = request.year, quarter = request.quarter, 
                                    department = d_key, course = ndb.Key(Course, request.course_id))
        print("Inserted the course under dept = ", d_key.get().name)
        schedule.put()
        return STORED_RESPONSES.items[message_ID]        
    
    '''OK'''
    # endpoint method to add schedule
    @endpoints.method(ADD_SCHEDULE_CONTAINER, responseMsg,
                      path='schedule/add', http_method='GET', name='schedule.add')
    def insertSchedule(self, request):
        ''' insert a course schedule for given quarter. Require course ID, quarter and year.'''
        response = ""
        # Validate course id 
        c_key = ndb.Key(Course, request.course_id)
        # Check if entity exists
        if c_key.get():
            # fetch the respective dept for that course id
            d_key = c_key.get().department
            
            # check for duplicate entries
            query = Schedule.query(Schedule.course == c_key, Schedule.quarter == request.quarter, 
                                   Schedule.year == request.year)
            if not query.get():
                # insert schedule
                response = self.upsertSchedule(request, d_key, ADD_ID)
            else:
                response = STORED_RESPONSES.items[DUPLICATE_ID]
        else:
            response = STORED_RESPONSES.items[INV_COURSE_ID]
        return response
    
    # endpoint method to delete a schedule
    @endpoints.method(REMOVE_SCHEDULE_CONTAINER, responseMsg,
                      path='schedule/delete', http_method='GET', name='schedule.delete')
    def deleteSchedule(self, request):
        ''' delete a schedule given course ID quarter and year'''
        try:
            # Get Course id
            c_key = ndb.Key(Course, int(request.course_id))
            print("deleteSchedule Method: Going to query object")
            # Get schedule id from given year, quarter and course
            query = Schedule.query(Schedule.course == c_key, Schedule.quarter == request.quarter, 
                                   Schedule.year == request.year)
            print("deleteSchedule method: After query = ", query)
            schedule = query.get() 
            if schedule:
                print("deleteSchedule method: schedule -",schedule.key," exists for course key = ", c_key)   
                # delete all enrollments for that schedule
                query = Enrollment.query(Enrollment.schedule == schedule.key)#ndb.Key(Schedule, schedule.id))
                for enrollment in query.fetch():
                    print("deleteSchedule Method: Fetching query = ", enrollment)
                    # delete course from Student model
                    student = enrollment.student.get()
                    print("===========Student list for course========", student)
                    if(c_key in student.study_lists):
                        student.study_lists.remove(c_key)
                        # update student entity
                        student.put()
                        print("deleteSchedule method: course not in student list")
                    print("deleteSchedule method: Going to delete enrollment with Key = ",enrollment.key)
                    # delete enrollment
                    #enrollment = q.get()
                    #ndb.Key(Enrollment, enrollment.id).delete()
                    enrollment.key.delete()
                    print("deleteSchedule method: deleted enrollment successfully")
                    #ndb.Key(Enrollment, q.id).delete()   
                # delete schedule
                schedule.key.delete()
        except:
            raise endpoints.EndpointsErrorMessage(
                 'Error while deleting a schedule.')
        
        return STORED_RESPONSES.items[DELETE_ID]
    
    ''' Functional Requirement:
    g. Allows user to list courses a department provides in a specific quarter
'''
    def queryToCoursesMessage(self, query):
        '''gets courses from query and puts in courses message'''
        cm = coursesMessage()
        for schedule in query.fetch():
            course = schedule.course.get()
            cm.courses.append(course.name)
        print("queryToCoursesMessages method: response message = ", cm.courses)
        return cm
    
    
    
    @endpoints.method(VIEW_DEPT_COURSES_CONTAINER, coursesMessage, 
                      path='schedule/coursesInDept', http_method='POST', name= 'student.coursesInDept')
    def view_dept_courses(self, request):
        ''' Allows user to list courses a department provides in a specific quarter'''
        d_key = ndb.Key(Department, request.department_id)
        query = Schedule.query(Schedule.department == d_key, Schedule.quarter == request.quarter,
                               Schedule.year == request.year)
        print("view_dept_courses method: converting query to messages")
        return self.queryToCoursesMessage(query)
    
        
# 5. Enrollments Api
'''
TO-DOs
1. Referential constraints on all the properties, student, course and quarter 
#2. Whenever an insert, update student study lists accordingly.
3. Whenever an update/delete in student record/course/quarter, this data needs to be deleted first and then the rest.
4. Why this table and not a join?? Data store doesn't support join operations, one has to go to relational model.
Add supporting doc: __________ 
'''    
@endpoints.api(name='enrollments', version='v1')
class EnrollmentsApi(remote.Service):
    '''
    Api for all operations of enrollments such as drop/enroll/view
    
    Assumption:
    1. course, year and quarter uniquely identifies a schedule in Schedule model
    '''            
    def getSchedule(self, course_key, quarter, year):
        return Schedule.query(Schedule.course == course_key, 
                               Schedule.quarter == quarter, Schedule.year == year)
    
    def getEnrollment(self, student_key, schedule_key):
        return Enrollment.query(Enrollment.student == student_key, Enrollment.schedule == schedule_key)
    
    @endpoints.method(ADD_ENROLLMENTS_CONTAINER, responseMsg,
                      path='enrollments/add', http_method='GET', name='enrollments.add')
    def insertEnrollment(self, request):
        ''' Enrollment a student for a course in a given quarter'''
        response = ""
        # validate all the Referential properties
        s_key = ndb.Key(Student, request.student_id)
        student = s_key.get()
        c_key = ndb.Key(Course, request.course_id)
        
        # retrieve schedule id from schedule
        query = self.getSchedule(c_key, request.quarter, request.year)
        schedule = query.get()
        
        # Check if schedule exists
        if schedule:
            schedule_key = schedule.key
        # query for existing enrollment. if student id and schedule id exists, duplicate entry 
            query = self.getEnrollment(s_key, schedule_key)
            enrollment = query.get()
            
            print("insertEnrollment method: Enrollment = ", enrollment)
            # check if enrollment exists already
            if not enrollment:
                # validate student ID
                if student:
                    # insert enrollment
                    enrollment = Enrollment(student = s_key, schedule = schedule_key)
                    enrollment.put()
                    
                    # add course to student study lists
                    student.study_lists.append(c_key)
                    student.put()
                    response = STORED_RESPONSES.items[ADD_ID]
                else:
                    # in valid student ID
                    response = STORED_RESPONSES.items[INV_STUDENT_ID]
            else:
                # enrollment already exists 
                response = STORED_RESPONSES.items[DUPLICATE_ID]
        else:
            response = STORED_RESPONSES.items[NOT_FOUND_ID]
        
        return response

    @endpoints.method(DELETE_ENROLLMENTS_CONTAINER, responseMsg,
                      path='enrollments/delete', http_method='GET', name='enrollments.delete')
    def deleteEnrollment(self, request):
        ''' Delete an enrollment of a course in a quarter for a student'''
        response = ""
        c_key = ndb.Key(Course, request.course_id)
        s_key = ndb.Key(Student, request.student_id)
        # fetch the key for given student, course and quarter
        query = self.getSchedule(c_key, request.quarter, request.year)
        # delete data in student study lists
        student = s_key.get()
        # check if entity found in Student model and has the course in study lists
        if student and (c_key in student.study_lists):
            print("deleteEnrollment Method: student study lists = ",student)
            student.study_lists.remove(c_key)
            student.put()
        # delete entity in enrollment
        query = self.getEnrollment(s_key, query.get().key)
        enrollment = query.get()
        if enrollment:
            enrollment.key.delete()
            response = STORED_RESPONSES.items[DELETE_ID]
        else:
            response = STORED_RESPONSES.items[NOT_FOUND_ID]
        
        return response
    
    
    '''
    Functional Requirement:
    e. Allows user to list students enrolled in a course'''
    def enrollmentToStudentsMessage(self, query):
        ''' method to get students from enrollments entity and copy to students message'''
        sm = studentsMessage()
        for enrollment in query.fetch():
            student = enrollment.student.get()
            sm.students.append(student.name)
        print("enrollmentToStudentMessage method: Students = ", sm.students)
        return sm
    @endpoints.method(VIEW_COURSE_STUDENTS_CONTAINER, studentsMessage, name='enrollments.viewStudentInCourse', 
                      path='enrollments/viewStudentInCourse', http_method='POST')
    def view_students_in_course(self, request):
        ''' List students enrolled in a course'''
        # fetch schedule ids containing the course listed
        c_key = ndb.Key(Course, request.course_id)
        query = Schedule.query(Schedule.course == c_key)
        schedule_keys  =[]
        for key in query.iter(keys_only=True):
            schedule_keys.append(key)
        # query for enrollments with matching schedule_keys
        query = Enrollment.query(Enrollment.schedule.IN(schedule_keys))
        print("view_students_in_course method: going to convert query to student names message")
        return    self.enrollmentToStudentsMessage(query)
#[END api]
    
    
    
# [START api_server]
api = endpoints.api_server([StudentApi, DepartmentApi, CourseApi, ScheduleApi, EnrollmentsApi])
# [END api_server]