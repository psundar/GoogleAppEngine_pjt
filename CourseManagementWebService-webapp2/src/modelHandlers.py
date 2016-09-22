#[START imports]
import webapp2
import json
from google.appengine.api import users
from google.appengine.ext.webapp import template


from data_models import Department
from data_models import Course
from data_models import Student
from data_models import Schedule
from data_models import Enrollment
from google.appengine.ext.key_range import ndb
from __builtin__ import True
from datetime import date
from google.storage.speckle.python.api.constants.FIELD_TYPE import YEAR
#[END imports]


#[START response message]
'''For iteration 2, replace this with json objects'''
R_SUCC_INSERT = "Successfully inserted {} data for key {} "
R_SUCC_DEL = "Successfully deleted {} data for key {} "
R_SUCC_UPD = "Successfully updated {} data for key {} "
R_INV_ID_ERR = "Invalid ID Error: ID not found for {}. Pleas check data and enter valid ID"
R_DUP_ID_ERR = "Duplicate ID Error: {} ID already found. ID needs to be unique. Please enter different value."
R_ID_VAL_ERR = "Value Error: {} ID needs to be an integer!"
R_PROP_VAL_ERR = "Value Error: Property {} need to be {}"
R_REQ_FIELD_ERR = "Null Value Error: These fields are required - ({})"
R_DEP_ERR_INVDEPT = "Dependency Error: Invalid Department ID. Please enter valid department"
R_DEP_ERR_INVCOUR = "Dependency Error: Invalid Course ID. Please enter valid course "
R_DEP_ERR_INVST = "Dependency Error: Invalid Student ID. Please enter a valid student ID"
R_DEP_ERR_INVSCH = "Dependency Error: Invalid Schedule ID. Please enter a valid schedule"
R_DEP_ERR_DELCHILD = "Child Dependency Error: Record found in {}. please delete {} from dependent entities" 
R_SERV_ERR = "Server Error: Message from server = {}"
R_CBOX_INP_ERR = "Input Error: No data is checked. Please check at least one record to delete"
R_RAD_INP_ERR = "Input Error: No data is selected. Please select one record"
#[END response message]

#[START Helper Functions]
def is_int(string):
        try:
            int(string)
            return True
        except ValueError:
            return False
#{END Helper Functions]


#[START Handlers]
''' Department Handler '''
class departmentHandler(webapp2.RequestHandler):
    def getDepartment(self, dept_id):
        ''' get department ndb record given a id'''
        d_key = ndb.Key(Department, dept_id)
        return d_key.get()
    
    def upsertDepartment(self, dept_id, dept_name):
        ''' Method to create/update a department entity'''
        department = Department(id=dept_id, department_id=dept_id, name=dept_name)
        dept_key = department.put()
        #print("Inserted a new dept")
        return dept_key
    
    def isValidID(self,dept_id):
        ''' Validates if department ID is an integer or not'''
        try:
            int(dept_id)
            return True
        except ValueError:
            return False
    
    def insertDept(self, dept_id, dept_name):
        # Check if both variables azre populated
        if dept_id and dept_name:
            # Check if department ID is an integer
            if(self.isValidID(dept_id)):
                # See if dept ID is already found in data store
                dept = self.getDepartment(dept_id)
                dept_key = None
                response = R_DUP_ID_ERR.format("Department")
                if not dept:
                    ''' New department record. Insert'''
                    #print "Department not found. Inserting new"
                    dept_key = self.upsertDepartment(int(dept_id), dept_name)
                    response = R_SUCC_INSERT.format("Department", str(dept_key)) 
            else:
                response = R_ID_VAL_ERR.format("Department")
        else:
            response = R_REQ_FIELD_ERR.format("dept ID and dept name")
        return response
    
    def deleteDept1(self, dept_id):
        ''' delete entity from department'''
        dept_key = ndb.Key(Department, dept_id)
        '''Check whether dept data is found in other dependent kinds before deleting'''
        
        dept_key.delete()
        return R_SUCC_DEL.format("Department",str(dept_id))
    def deleteDept(self, dept_id):
        ''' delete department given department ID. delete in the order Schedule, Student and Course first'''
        # Enhancement. Deleting entity using other details like department name
        try:
            # Creating the key for given department id
            d_key = ndb.Key(Department, int(dept_id))
            # Fetching and deleting the entity
            dept = Department.get_by_id(dept_id)
            ''' Dependencies'''
            # check if department exists in Student kind
            st_query = Student.query(Student.department == d_key)
            co_query = Course.query(Course.department == d_key)
            sch_query = Schedule.query(Schedule.department == d_key)
            if sch_query.get():
                # entity found in Schedule. Invoke Dependency error
                response = R_DEP_ERR_DELCHILD.format("Schedule", "Department")
            elif st_query.get():
                # entity found in Student. Invoke Dependency error
                response = R_DEP_ERR_DELCHILD.format("Student", "Department")
            elif co_query.get():
                # entity found in Course. Invoke Dependency error
                response = R_DEP_ERR_DELCHILD.format("Course", "Department")
            else:
                # no dependencies found. delete department
                d_key.delete()
                response = R_SUCC_DEL.format("Department", str(d_key))
        
        except Exception, e:
            response = R_SERV_ERR.format(str(e)) 
        return response
            
    def render_main(self, department="", dept_id="",error="No Errors!"):
        ''' Method to render the main page for department'''
        department = ndb.gql("SELECT * FROM Department\
                                    ORDER BY department_id")
        data = {}
        for depts in department:
            data[depts.department_id]=depts.name
        print 'JSON: ', data
        values = {'department' : department,
                  'error': error,
                  'dept_id': dept_id,
                  'jsonData':data}
        self.response.out.write(template.render('main.html', values))
    
    def render_edit(self, department=""):
        values = {'department': department}
        self.response.out.write(template.render('dept_edit.html', values))
    
    def get(self):
        # defining a GQL query to get all the inserted data for deparment
        user = users.get_current_user()
        if user:
            #print("rendering main page")
            self.render_main()
        else:
            self.redirect(users.create_login_url(self.request.uri))
    
    def post(self):
        insert = self.request.get('insert')
        delete = self.request.get('delete')
        edit = self.request.get('edit')
        save = self.request.get('save')
        if insert:
            '''Insert button was pressed'''
            dept_id = self.request.get('dept_id')
            dept_name = self.request.get('dept_name')
            response = self.insertDept(int(dept_id), dept_name) 
            self.render_main(error=response, dept_id=dept_id)    
        elif delete:
            '''Delete button was pressed'''
            message = ""
            delCheckBox = self.request.get('deleteCheck', allow_multiple=True)
            if delCheckBox:
                for d_id in delCheckBox:
                    message = message+ self.deleteDept(int(d_id))
                #errors = {'error':"Yet to implement delete method. But you reached step 1!"}
            else:
                message = R_CBOX_INP_ERR
            self.render_main(error=message)
        elif edit:
            ''' Edit button was pressed'''
            message = ""
            d_id = self.request.get('editRadio')
            if d_id:
                dept = self.getDepartment(int(d_id))
                if dept:
                    self.render_edit(department=dept)
                else:
                    message = R_SERV_ERR.format("Unable to retrieve data from Department")
                    self.render_main(error=message)
            else:
                message = R_RAD_INP_ERR
                self.render_main(error=message)
        elif save:
            ''' Save after edit'''
            message = ""
            dept_id = self.request.get('dept_id')
            dept_name = self.request.get('dept_name')
            response = self.upsertDepartment(int(dept_id), dept_name) 
            response = R_SUCC_UPD.format("Department"+str(response)) 
            self.render_main(error = response, dept_id=dept_id)  
        #self.response.out.write('added new department')

''' Course Handler'''
class courseHandler(webapp2.RequestHandler):
    def getCourse(self, course_id):
        ''' return course entity given ID'''
        c_key = ndb.Key(Course, course_id)
        return c_key.get()
    
    def getDepartment(self, dept_id):
        ''' Get department entity given department ID'''
        dept_key = ndb.Key(Department, dept_id)
        return dept_key.get()    
    
    def upsertCourse(self, course_id, name, dept_id, instructor, time, place):
        ''' insert or update course entity'''
        course = Course(id=course_id, course_id=course_id, name = name, department = ndb.Key(Department, dept_id) , 
                                    instructor=instructor, time = time, place=place)
        course_key = course.put()
        return course_key
        
    def insertCourse(self, request):
        ''' insert a new course given course ID and department ID. course ID is unique across depts.'''
        response = ""
        try:
            course_id = request.get('course_id')
            name = request.get('course_name')
            dept_id = request.get('dept_id')
            instructor = request.get('instructor')
            time = request.get('time')
            place = request.get('place')
            # Check if required fields are not empty
            if(course_id and dept_id):
                course_id = int(course_id)
                dept_id = int(dept_id)
                course = self.getCourse(course_id)
                # check for valid department
                department = self.getDepartment(dept_id)
                # Course Not found. Insert new course
                if not course:
                    # Validate department
                    if department:
                        # create new course 
                        c_id = self.upsertCourse(course_id=course_id, name=name, dept_id=dept_id, instructor=instructor, time=time, place=place)
                        response = R_SUCC_INSERT.format("course",str(c_id))
                    else:
                        response = R_DEP_ERR_INVDEPT
                else:
                    # Course found. cannot insert but update 
                    response = R_DUP_ID_ERR.format("course") 
            else:
                response = R_REQ_FIELD_ERR.format("Course ID and Department ID")
        except Exception, e:
            response = R_SERV_ERR.format(str(e))
        
        return response
    
    def deleteCourse(self, course_id):
        '''Delete a course given course ID. Delete course from Schedule first.'''
        try:
            response = ""
            # Creating the key for given course id
            c_key = ndb.Key(Course, course_id)
            # Check if course exists
            if c_key.get():
                '''Dependency Check'''
                # Check if course exists in schedule
                query = Schedule.query(Schedule.course == c_key)
                if query.get():
                    # course exists in schedule. Invoke dependency error
                    response = R_DEP_ERR_DELCHILD.format("Schedule","Course")
                else: 
                    # Fetching and deleting the entity with given course_id 
                    c_key.delete()
                    response = R_SUCC_DEL.format("Course",str(c_key))
        except Exception, e:
            response = R_SERV_ERR.format(str(e))
        return response
    
    
    def render_coursepage(self, courses="", error="", course_id=""):
        ''' Method to render course dashboard page'''
        courses = ndb.gql("SELECT * FROM Course\
                                    ORDER BY course_id")
        # packaging into json object for <iteration 2> API Backend
        jsonData = {}
        for course in courses:
            jsonData['course.course_id'] = course.name
        values = {'courses' : courses,
                  'error': error,
                  'course_id': course_id,
                  'jsonData':jsonData}
        self.response.out.write(template.render('course.html', values))
    
    def render_edit(self, course):
        ''' Method to edit Course data'''
        # Get department ID from key
        dept_id = course.department.id()
        values = {'course': course,
                  'dept_id': dept_id}
        self.response.out.write(template.render('course_edit.html', values))
        
    
    def get(self):
        user = users.get_current_user()
        if user:
            #print("rendering main page")
            self.render_coursepage()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
    def post(self):
        insert = self.request.get('insert')
        delete = self.request.get('delete')
        edit = self.request.get('edit')
        save = self.request.get('save')
        if insert:
            ''' Insert button pressed'''
            response = self.insertCourse(self.request)
            self.render_coursepage(error=response, course_id=self.request.get('course_id'))
            
        elif delete:
            ''' Delete button pressed'''
            response = ""
            delCheck = self.request.get('deleteCheck', allow_multiple=True)
            if(delCheck):
                for c_id in delCheck:
                    response = response+self.deleteCourse(int(c_id))
            else:
                response = R_CBOX_INP_ERR
            self.render_coursepage(error=response)
        elif edit:
            ''' Edit button pressed'''
            response = ""
            c_id = self.request.get('editRadio')
            # Check if radio button was pressed
            if(c_id):
                course = self.getCourse(int(c_id))
                if(course):
                    # if course data exists in data store, redirect to edit page
                    self.render_edit(course=course)
                else:
                    response = R_SERV_ERR.format("Unable to retrieve data from server!")
                    self.render_coursepage(error=response)
            else:
                # Nothing was selected
                response = R_RAD_INP_ERR
                self.render_coursepage(error=response)
            
        elif save:
            ''' Save button pressed'''
            # read all input
            course_id = self.request.get('course_id')
            course_name = self.request.get('course_name')
            dept_id = self.request.get('dept_id')
            instructor = self.request.get('instructor')
            time = self.request.get('time')
            place = self.request.get('place')
            # Check if department id is not blank
            if(dept_id):
                # validate department id
                dept_id = int(dept_id)
                course_id = int(course_id)
                if(self.getDepartment(dept_id)):
                    c_key = self.upsertCourse(course_id = course_id, name = course_name, dept_id = dept_id, instructor = instructor, time = time, place = place)
                    response = R_SUCC_UPD.format("Course",str(c_key))
                else:
                    response = R_DEP_ERR_INVDEPT
            else:
                response = R_REQ_FIELD_ERR.format("Department ID is required")
            self.render_coursepage(error=response)

''' Student Handler'''
class studentHandler(webapp2.RequestHandler):
    
    def getStudent(self, student_id):
        ''' get student entity given ID'''
        s_key = ndb.Key(Student, student_id)
        return s_key.get()
    
    def getDepartment(self, dept_id):
        ''' get department entity given department ID'''
        dept_key = ndb.Key(Department, dept_id)
        return dept_key.get()
    
    def upsertStudent(self, student_id, name, dept_id, phone_number, address):
        ''' insert or update Student entity'''
        student = Student(id=student_id, student_id=student_id, name=name, 
                          address=address, phone_number=phone_number, 
                          department=ndb.Key(Department, dept_id))
        #print("Inserting a new record into the datastore",student.put())
        s_key = student.put()
        return R_SUCC_INSERT.format("Student", str(s_key)) 
    
    
    def insertStudent(self, request):
        ''' Insert student entity given student ID'''
        try:
            response = ""
            # get all parameters
            student_id = request.get('student_id')
            student_name = request.get('student_name')
            address = request.get('address')
            phone_number = request.get('phone_number')
            dept_id = request.get('dept_id')
            
            # check if required fields are not blank
            if(student_id and student_name and dept_id):
                # check if IDs are all integers
                if(is_int(student_id) and is_int(dept_id)):
                    student_id = int(student_id)
                    dept_id = int(dept_id)
                    # check if phone number is either blank or if entered is all numbers of length 10
                    if((not phone_number) or (phone_number and is_int(phone_number) and len(phone_number)==10)):
                        # Check if student id already exists
                        student = self.getStudent(student_id)
                        if not student:
                            # Check if department is valid 
                            dept = self.getDepartment(dept_id) 
                            if(not dept):
                                # Invalid department id
                                #print("Department record not found!", dept)
                                response = R_DEP_ERR_INVDEPT
                            else:
                                #print("New student record to be added",student)
                                # find if phone number is blank, then insert None
                                if(phone_number):
                                    phone_number = int(phone_number)
                                else:
                                    phone_number = int()   
                                # insert student entity
                                response = self.upsertStudent(student_id=student_id, name=student_name, dept_id = dept_id, phone_number=phone_number, address=address)
                            
                        else:
                            #Send Error Message
                            response = R_DUP_ID_ERR.format("Student")
                    else:
                        response = R_PROP_VAL_ERR.format("Phone Number", "number of length 10") 
                else:
                    response = R_ID_VAL_ERR.format("Department and Student")
            else:
                response = R_REQ_FIELD_ERR.format("Student ID, Student Name and Dept ID")
        except Exception, e:
            response = R_SERV_ERR.format(str(e))
        return response
    
    def deleteStudent(self, student_id):
        ''' Delete student entity given student id'''
        try:
            response = ""
            # Create a key for given student id
            s_key = ndb.Key(Student, student_id)
            # Fetching student entity
            #student = Student.get_by_id(student_id)
            #print ("Student Record to be deleted = ", student)
            
            if s_key.get():
                # check if the student is enrolled in a course or not. 
                query = Enrollment.query(Enrollment.student == s_key)
                if query.get():
                    # cannot delete student without deleting his enrollments
                    response = R_DEP_ERR_DELCHILD.format("Enrollments", "Student")
                else:
                    # deleting the entity with a given student id
                    s_key.delete()
                    response = R_SUCC_DEL.format("Student", str(s_key))
            else:
                response = R_SERV_ERR.format("Unable to retrieve Student entity")
         
        except Exception, e:
            response = R_SERV_ERR.format(str(e))
        return response
    """
    def copyToCoursesMessage(self, study_lists):
        print("Inside copyToCourseMessage method")
        cm = coursesMessage()
        for c in study_lists:
            cm.courses.append(c.get().name)
        print("copyToCoursesMessage method: courses =", cm)
        return cm
    
    def view_courses_by_student(self, request):
        ''' List courses a student enrolls in'''
        # Validate student id
        s_key = ndb.Key(Student, request.student_id)
        study_lists = None
        if s_key:
            study_lists = s_key.get().study_lists
            # access structured property, form messages and return them
        #print("Inside view_courses_by_student method")
        return self.copyToCoursesMessage(study_lists)
    """
    def render_student(self, student="", student_id="",error="No Errors!"):
        ''' Method to render the main page for department'''
        students = ndb.gql("SELECT * FROM Student\
                                    ORDER BY student_id")
        
        values = {'students' : students,
                  'error': error,
                  'student_id': student_id
                  }
        self.response.out.write(template.render('student.html', values))
    
    def render_edit(self, student=""):
        ''' editing student entity page'''
        # get department id from key
        dept_id = student.department.id()
        values = {'student': student,
                  'dept_id': dept_id}
        self.response.out.write(template.render('student_edit.html', values))
    
    def get(self):
        user = users.get_current_user()
        if user:
            self.render_student()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
        
    def post(self):    
        insert = self.request.get('insert')
        delete = self.request.get('delete')
        edit = self.request.get('edit')
        save = self.request.get('save')
        
        if(insert):
            ''' insert button was pressed'''
            response = self.insertStudent(self.request)
            self.render_student(error=response)
            
        elif(delete):
            ''' delete button was pressed'''
            # check if atleast one checkbox is checked
            delCheck = self.request.get('deleteCheck', allow_multiple =True)
            if(delCheck):
                for s_id in delCheck:
                    response = self.deleteStudent(int(s_id))
            else:
                response = R_CBOX_INP_ERR
            self.render_student(error=response)    
        elif(edit):
            ''' edit button was pressed'''
            # read ID from radio button
            s_id = self.request.get('editRadio')
            # check if radio button is selected or not
            if(s_id):
                student = self.getStudent(int(s_id))
                self.render_edit(student=student)
            else:
                response = R_RAD_INP_ERR 
                self.render_student(error=response)
            
        elif(save):
            ''' save button was pressed from the edit html page'''
            # read all input
            student_id = int(self.request.get('student_id'))
            student_name = self.request.get('student_name')
            address = self.request.get('address')
            phone_number = self.request.get('phone_number')
            dept_id = self.request.get('dept_id')
            
            # check if required fields are populated
            if(student_name and dept_id):
            # validate inputs
                if(is_int(dept_id)):
                    dept_id = int(dept_id)
                    if(self.getDepartment(dept_id)):
                        if((not phone_number) or (is_int(phone_number) and len(phone_number)==10)):
                            if(not phone_number):
                                phone_number = int()
                            else:
                                phone_number = int(phone_number)
                        # call upsert method
                            response = self.upsertStudent(student_id=student_id, name=student_name, dept_id=dept_id, phone_number=phone_number, address=address)
                        else:
                            response = R_PROP_VAL_ERR.format("Phone number", "integer of length 10")
                    else:
                        response = R_DEP_ERR_INVDEPT
                else:
                    response = R_ID_VAL_ERR.format("Department")    
                
            else:
                response = R_REQ_FIELD_ERR.format("Student Name and Dept ID")
            
            # render the main page
            self.render_student(error=response)
            
''' Schedule Handler'''
class scheduleHandler(webapp2.RequestHandler):
    
    def upsertSchedule(self, year, quarter, d_key, course_id):
        ''' insert or update Schedule entity'''
        schedule = Schedule(year = year, quarter = quarter, 
                                    department = d_key, course = ndb.Key(Course, course_id))
        #print("Inserted the course under dept = ", d_key.get().name)
        sch_key = schedule.put()
        return R_SUCC_INSERT.format("Schedule", str(sch_key))        
    
    def validate_year(self, year):
        # if year is in string
        year = int(year)
        currYear = date.today().year
        return (year >= (currYear - 1) and year <= (currYear + 1))
    
    def validate_quarter(self, quarter):
        quarter = int(quarter)
        return quarter in [1,2,3,4]
    
    '''OK'''
    def insertSchedule(self, request):
        ''' insert a course schedule for given quarter. Require course ID, quarter and year.'''
        response = ""
        # read all inputs
        course_id = request.get('course_id')
        year = request.get('year')
        quarter = request.get('quarter')
        
        # check if required fields are not blank
        if(course_id and year and quarter):
            # validate inputs
            if(is_int(course_id) and is_int(year) and is_int(quarter)):
                course_id = int(course_id)
                year = int(year)
                quarter = int(quarter)
                # validate inputs continued
                # Get current year
                
                # Year needs to be prev, curr and next year
                if(self.validate_year(year) and self.validate_quarter(quarter)):
                    # Validate course id 
                    c_key = ndb.Key(Course, course_id)
                    # Check if entity exists
                    if c_key.get():
                        # fetch the respective dept for that course id
                        d_key = c_key.get().department
                        
                        # check for duplicate entries
                        query = Schedule.query(Schedule.course == c_key, Schedule.quarter == quarter, 
                                               Schedule.year == year)
                        if(not query.get()):
                            # insert schedule
                            response = self.upsertSchedule(year=year, quarter=quarter, d_key=d_key, course_id=course_id)
                        else:
                            response = R_DUP_ID_ERR.format("Schedule")
                    
                    else:
                        response = R_DEP_ERR_INVCOUR
                else:
                    response = R_PROP_VAL_ERR.format("Year and Quarter", "integers of values (previous year, current year and next year) and range(1-4) respectively")
            else:
                response = R_ID_VAL_ERR.format("Course ID and Year and Quarter")
        else:
            response = R_REQ_FIELD_ERR.format("Course ID and Year and Quarter")
        return response
    
    def deleteSchedule(self, schedule):
        ''' delete a schedule given course ID quarter and year'''
        try:
            # Get Course id
            c_key = schedule.course
            # Get schedule id from given year, quarter and course
            '''query = Schedule.query(Schedule.course == c_key, Schedule.quarter == int(schedule.quarter), 
                                   Schedule.year == int(schedule.year))
            print("deleteSchedule method: After query = ", query)
            schedule = query.get() '''
            if schedule:
                # print("deleteSchedule method: schedule -",schedule.key," exists for course key = ", c_key)   
                # delete all enrollments for that schedule
                query = Enrollment.query(Enrollment.schedule == schedule.key)#ndb.Key(Schedule, schedule.id))
                for enrollment in query.fetch():
                #    print("deleteSchedule Method: Fetching query = ", enrollment)
                    # delete course from Student model
                    student = enrollment.student.get()
                    #print("===========Student list for course========", student)
                    if(c_key in student.study_lists):
                        student.study_lists.remove(c_key)
                        # update student entity
                        student.put()
                    #       print("deleteSchedule method: course not in student list")
                    #print("deleteSchedule method: Going to delete enrollment with Key = ",enrollment.key)
                    # delete enrollment
                    #enrollment = q.get()
                    #ndb.Key(Enrollment, enrollment.id).delete()
                    enrollment.key.delete()
                    #print("deleteSchedule method: deleted enrollment successfully")
                    #ndb.Key(Enrollment, q.id).delete()   
                # delete schedule
                schedule.key.delete()
                response = R_SUCC_DEL.format("Schedule", str(schedule.year)+"-"+str(schedule.quarter)+"-"+str(schedule.course_id))
            else:
                response = R_SERV_ERR.format("Unable to read data from Schedule Entity")
        except Exception, e:
            response = R_SERV_ERR.format(str(e))
        
        return response
    
    def render_schedule(self, schedule="", error=""):
        ''' Schedule dashboard page'''
        schedule = ndb.gql("SELECT * FROM Schedule\
                                    ORDER BY year")
        values = {'schedules': schedule,
                  'error': error}
        self.response.out.write(template.render("schedule.html", values))
    
    def render_edit(self, schedule=""):
        ''' editing schedule entity page'''
        #self.response.out.write("Schedule = "+str(schedule))
        dept_id = schedule.department.id()
        course_id = schedule.course.id()
        values = {'dept_id': dept_id,
                  'course_id': course_id,
                  'schedule': schedule}
        self.response.out.write(template.render('schedule_edit.html', values))
        
    def get(self):
        user = users.get_current_user()
        if user:
            self.render_schedule()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
        
    def post(self):    
        insert = self.request.get('insert')
        delete = self.request.get('delete')
        edit = self.request.get('edit')
        save = self.request.get('save')
        
        if(insert):
            ''' insert button was pressed'''
            # insert 
            response = self.insertSchedule(self.request)
            # render main page
            self.render_schedule( error=response)
        elif(delete):
            ''' delete button was pressed'''
            response = ""
            # check if atleast one checkbox checked
            delCheck = self.request.get('deleteCheck', allow_multiple=True)
            if(delCheck):
            # call delete method
                for sch in delCheck:
                    # get ndb model key from urlsafe string
                    sch_key = ndb.Key(urlsafe=sch)
                    response = response + self.deleteSchedule(sch_key.get())+"\n"
            # if not checked return error message
            else:
                response = R_CBOX_INP_ERR
            self.render_schedule( error=response)
        elif(edit):
            ''' edit button was pressed'''
            # read ID from radio button
            sch = self.request.get('editRadio')
            # check if one radio is selected or not
            if(sch):
                # get key from url safe key string
                sch_key = ndb.Key(urlsafe=sch)
                
            # render edit page
                self.render_edit(schedule=sch_key.get())
            # if none selected return error message and render main
            else:
                response = R_RAD_INP_ERR
                self.render_schedule( error=response)
        elif(save):
            ''' save button was pressed from the edit html page'''
            response = ""
            # read all input
            year = self.request.get('year')
            quarter = self.request.get('quarter')
            sch_key = ndb.Key( urlsafe=self.request.get('sch_key') )
            # check if required fields are not blank
            if(year and quarter):
                #validate inputs
                if(is_int(year) and self.validate_year(year) and is_int(quarter) and self.validate_quarter(quarter)):
                    schedule = sch_key.get()
                    # update fields
                    schedule.year = int(year)
                    schedule.quarter = int(quarter)
                    # store back to datastore
                    schedule.put()
                    response = R_SUCC_UPD.format("Schedule", str(sch_key))
                else:
                    response = R_PROP_VAL_ERR.format("Year and Quarter", "integers of values (previous year, current year and next year) and range(1-4) respectively")
            else:
                response = R_REQ_FIELD_ERR.format("Year and Quarter")
            '''
            course_id = self.request.get('course_id')
            # check if required fields are populated
            if(year and quarter and course_id):
            # validate inputs
                if(is_int(course_id) and is_int(year) and is_int(quarter)):
                    course_id = int(course_id)
                    year = int(year)
                    quarter = int(quarter)
                    if(year in range(1900, 2017) and quarter in [1,2,3,4]):
                        # get dept Id for the given course ID
                        c_key = ndb.Key(Course, course_id)
                        d_key = c_key.get().department
                        
                        # call upsert method
                        
                        response = self.upsertSchedule(year=year, quarter=quarter, d_key = d_key, course_id = course_id)
                    else:
                        response = R_PROP_VAL_ERR.format("Year and Quarter", "integers of value between (1900-2017) and (1-4) respectively")
                else:
                    response = R_ID_VAL_ERR.format("Year and Quarter and Course ID") 
            else:
                response = R_REQ_FIELD_ERR.format("Year and Quarter and Course ID")
                '''
            # render the main page
            #self.response.out.write('To save!')
            self.render_schedule(error=response)    

''' Enrollments Handler'''
class enrollmentsHandler(webapp2.RequestHandler):
    
    def getSchedule(self, course_key, quarter, year):
        return Schedule.query(Schedule.course == course_key, 
                               Schedule.quarter == quarter, Schedule.year == year)
    
    def getEnrollment(self, student_key, schedule_key):
        return Enrollment.query(Enrollment.student == student_key, Enrollment.schedule == schedule_key)
    
    def insertEnrollment(self, request):
        ''' Enrollment a student for a course in a given quarter'''
        response = ""
        
        # read all input variables
        student_id = request.get('student_id')
        course_id = request.get('course_id')
        year = request.get('year')
        quarter = request.get('quarter')
        
        # check for required fields
        if(student_id and course_id and year and quarter):
        
            # validate inputs
            if(is_int(student_id) and is_int(course_id)):
                if(is_int(year) and is_int(quarter)):
                           
                    student_id = int(student_id)
                    course_id = int(course_id)
                    year = int(year)
                    quarter = int(quarter)
                    # validate all the Referential properties
                    s_key = ndb.Key(Student, student_id)
                    student = s_key.get()
                    c_key = ndb.Key(Course, course_id)
                    
                    # retrieve schedule id from schedule
                    query = self.getSchedule(c_key, quarter, year)
                    schedule = query.get()
                    
                    # Check if schedule exists
                    if schedule:
                        #schedule_key = schedule.key
                    # query for existing enrollment. if student id and schedule id exists, duplicate entry 
                        query = self.getEnrollment(s_key, schedule.key)
                        enrollment = query.get()
                        
                        # check if enrollment exists already
                        if not enrollment:
                            # validate student ID
                            if student:
                                # insert enrollment
                                enrollment = Enrollment(student = s_key, schedule = schedule.key)
                                e_key = enrollment.put()
                                
                                # add course to student study lists
                                student.study_lists.append(c_key)
                                student.put()
                                response = R_SUCC_INSERT.format("Enrollments", str(e_key))
                            else:
                                # in valid student ID
                                response = R_DEP_ERR_INVST
                        else:
                            # enrollment already exists 
                            response = R_DUP_ID_ERR.format("Enrollment")
                    else:
                        response = R_INV_ID_ERR.format("Enrollments")
                
                else:
                    response = R_PROP_VAL_ERR.format("Year and Quarter", "integers of values (previous year, current year and next year) and range(1-4)")
            else:
                response = R_ID_VAL_ERR.format("Student and Course")
        else:
            response = R_REQ_FIELD_ERR.format("Student ID, Course ID, Year and Quarter")
        return response

    def deleteEnrollment(self, enrollment):
        ''' Delete an enrollment of a course in a quarter for a student'''
        response = ""
        if(not enrollment):
            return R_INV_ID_ERR.format("Enrollments")
        # read all inputs
        student_id = enrollment.student.id()
        schedule = enrollment.schedule.get()
        course_id = schedule.course.id()
        year = schedule.year
        quarter = schedule.quarter
        
        # since checkbox inputs, no need to validate integer values and valid data
        c_key = schedule.course
        s_key = enrollment.student
        # delete data in student study lists
        student = s_key.get()
        # check if entity found in Student model and has the course in study lists
        if student and (c_key in student.study_lists):
            #print("deleteEnrollment Method: student study lists = ",student)
            student.study_lists.remove(c_key)
            student.put()
            enrollment.key.delete()
            response = R_SUCC_DEL.format("Enrollments", str(enrollment.key))
        
        return response
    
    def render_enrollments(self, error="", enrollment=""):
        ''' render Enrollments dashboard page'''
        
        enrollments = ndb.gql("SELECT * FROM Enrollment")
        enroll_info = list()
        record = dict()
        for enrollment in enrollments:
            record = {'schedule': enrollment.schedule.get(),
                      'student': enrollment.student.get(),
                      'e_key': enrollment.key}
            #print enrollment
            enroll_info.append([record])
        values = {'enrollments': enroll_info,
                  'error': error
                  }
        self.response.out.write(template.render('enrollments.html', values))
        #self.response.out.write(values)
    
    def render_edit(self, enrollment=""):
        ''' editing enrollment entity page'''
        #self.response.out.write("Schedule = "+str(schedule))
        schedule = enrollment.schedule.key.get() 
        dept_id = schedule.department.id()
        course_id = schedule.course.id()
        student_id = enrollment.student.id()
        values = {'dept_id': dept_id,
                  'course_id': course_id,
                  'student_id': student_id,
                  'enrollment': enrollment}
        self.response.out.write(template.render('schedule_edit.html', values))

    def get(self):
        user = users.get_current_user()
        if user:
            self.render_enrollments(error="No Errors!")
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
    def post(self):    
        insert = self.request.get('insert')
        delete = self.request.get('delete')
        """edit = self.request.get('edit')
        save = self.request.get('save')"""
        
        if(insert):
            ''' insert button was pressed'''
            # insert 
            response = self.insertEnrollment(self.request)
            # render main page
            self.render_enrollments(error = response)
        elif(delete):
            ''' delete button was pressed'''
            response = ""
            # check if atleast one checkbox checked
            delCheck = self.request.get('deleteCheck', allow_multiple=True)
            # call delete method
            if(delCheck):
                for e_key in delCheck:
                    e_key = ndb.Key(urlsafe=e_key)
                    #e_key = record['e_key']
                    response = response+self.deleteEnrollment(e_key.get())+"\n"
            else:
                response = R_CBOX_INP_ERR
            # if not checked return error message
            self.render_enrollments(error=response)
        """    
        elif(edit):
            ''' edit button was pressed'''
            # read all input
            
            # check if required fields are populated
            
            # validate inputs
            
            # call upsert method
            
            # render the main page
            self.response.out.write('To edit!')
        elif(save):
            ''' save button was pressed from the edit html page'''
            # read ID from radio button
            
            # check if one radio is selected or not
            
            # render edit page
            
            # if none selected return error message and render main
            self.response.out.write('To save!')  
            """      
#[END Handlers] 