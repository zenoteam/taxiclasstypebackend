from classtype_backend.app import create_app
from classtype_backend.models import ClasstypeModel
from datetime import date, datetime

if __name__ == '__main__':
    application = create_app()
    application.app_context().push()

    # Create some test data
    test_data = [("Class A", 'Something about the class', datetime.now()),
                 ("Class B", 'Something about the class', datetime.now()),
                 ("Class C", 'Something about the class', datetime.now()),
                 ("Class D", 'Something about the class', datetime.now())]
    for class_name, class_description, date in test_data:
        classTypes = ClasstypeModel(class_name=class_name,
                                    class_description=class_description,
                                    timestamp=date)
        application.db.session.add(classTypes)

    application.db.session.commit()
