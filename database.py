from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey

Base = declarative_base()

# utils
def opendb():
    engine = create_engine('sqlite:///database.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def save(obj):
    session = opendb()
    session.add(obj)
    session.commit()
    session.close()

def get_all(obj):
    session = opendb()
    return session.query(obj).all()


# classes User, Exam, Question, Attempt, ProctorLog
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    email = Column(String)
    name = Column(String)
    surname = Column(String)
    role = Column(String, default='student')
    is_banned = Column(Boolean, default=False)

class Exam(Base):
    __tablename__ = 'exams'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    duration = Column(Integer, default=60)
    passing_score = Column(Float, default=70)
    total_score = Column(Float, default=100)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime)

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey('exams.id'))
    question = Column(String)
    option_a = Column(String)
    option_b = Column(String)
    option_c = Column(String)
    option_d = Column(String)
    correct_option = Column(String)
    marks = Column(Float, default=10)
    created_at = Column(DateTime)

class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    exam_id = Column(Integer, ForeignKey('exams.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    attempt_id = Column(Integer, ForeignKey('attempts.id'))
    answer = Column(String)
    is_correct = Column(Boolean, default=False)
    created_at = Column(DateTime)

class Attempt(Base):
    __tablename__ = 'attempts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    exam_id = Column(Integer, ForeignKey('exams.id'))
    score = Column(Float, default=0)
    is_passed = Column(Boolean, default=False)
    is_submitted = Column(Boolean, default=False)
    is_cheated = Column(Boolean, default=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime)

class ProctorLog(Base):
    __tablename__ = 'proctor_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    exam_id = Column(Integer, ForeignKey('exams.id'))
    attempt_id = Column(Integer, ForeignKey('attempts.id'))
    recording = Column(String)
    status = Column(Integer, default=0)
    created_at = Column(DateTime)

# create tables
def create_tables():
    engine = create_engine('sqlite:///database.db')
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_tables()
    print('Tables created successfully')

