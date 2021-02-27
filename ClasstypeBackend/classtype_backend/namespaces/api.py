import http.client
from datetime import datetime, timedelta

from flask import abort
from flask_restplus import Namespace, Resource, fields
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from classtype_backend import config
from classtype_backend.db import db
from classtype_backend.models import ClasstypeModel
from classtype_backend.token import validate_token_header

api = Namespace('api', description='General API operations')


def authentication_header_parser(value):
    payload = validate_token_header(value, config.PUBLIC_KEY)
    if payload is None:
        abort(401)
    return payload


def check_admin_return_payload(parser, super=False):
    args = parser.parse_args()
    tokenPayload = authentication_header_parser(args['Authorization'])

    # check if user is an admin
    if 'admin' not in tokenPayload:
        abort(403)

    # for super admin
    if super:
        if tokenPayload['admin'] != 1:
            abort(403)

    return tokenPayload


# Output formats
model = {
    'id': fields.Integer(),
    "class_name": fields.String(),
    "class_description": fields.String(),
    "updateTimestamp": fields.DateTime(),
    "timestamp": fields.DateTime
}
classTypesModel = api.model('Classtype', model)

# Input formats
authenticationParser = api.parser()
authenticationParser.add_argument('Authorization',
                                  location='headers',
                                  type=str,
                                  help='Bearer Access Token')

classTypesParser = authenticationParser.copy()
classTypesParser.add_argument('class_name',
                              type=str,
                              required=True,
                              help='The class_name')
classTypesParser.add_argument('class_description',
                              type=str,
                              required=True,
                              help='The class description')

updateParser = classTypesParser.copy()
updateParser.replace_argument('class_name',
                              type=str,
                              required=False,
                              help='The new name of the class')
updateParser.replace_argument('class_description',
                              type=str,
                              required=False,
                              help='The new class description')

dateQuery_parser = authenticationParser.copy()
dateQuery_parser.add_argument('startdate',
                              type=str,
                              required=True,
                              help="The start date format '%d/%m/%Y'")
dateQuery_parser.add_argument('enddate',
                              type=str,
                              required=True,
                              help="The end date format '%d/%m/%Y'")

monthQuery_parser = authenticationParser.copy()
monthQuery_parser.add_argument('year',
                               type=str,
                               required=True,
                               help='The year')

filter_parser = authenticationParser.copy()
filter_parser.add_argument('search',
                           type=str,
                           required=False,
                           help='class type name')


@api.route('/classTypes/')
class ClasstypeList(Resource):
    @api.doc('list_classTypes')
    @api.marshal_with(classTypesModel, as_list=True)
    @api.expect(filter_parser)
    def get(self):
        """
        Retrieve all classTypes
        """
        args = filter_parser.parse_args()
        authentication_header_parser(args['Authorization'])

        query = ClasstypeModel.query
        if args['search']:
            search_param = args['search']
            param = f'%{search_param}%'
            query = (query.filter(ClasstypeModel.class_name.ilike(param)))

        query = query.order_by('id')
        classTypes = query.all()

        return classTypes

    @api.doc('create_classTypes')
    @api.expect(classTypesParser)
    def post(self):
        """
        Create a new classTypes, only accessible by super classTypes.
        """
        # authenticate bearer token
        check_admin_return_payload(classTypesParser, super=True)

        args = classTypesParser.parse_args()

        classTypes = (ClasstypeModel.query.filter(
            ClasstypeModel.class_name == args['class_name']).first())
        if classTypes:
            result = {
                'result':
                'Auth Id has already been used to create an classTypes'
            }
            return result, http.client.UNPROCESSABLE_ENTITY

        newClasstype = ClasstypeModel(
            class_name=args["class_name"],
            class_description=args["class_description"],
            timestamp=datetime.utcnow())

        db.session.add(newClasstype)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return '', http.client.UNPROCESSABLE_ENTITY

        result = api.marshal(newClasstype, classTypesModel)

        return result, http.client.CREATED


@api.route('/classTypes/<int:classTypesId>/')
class Classtype(Resource):
    @api.doc('retrieve_classTypes')
    @api.marshal_with(classTypesModel)
    @api.expect(authenticationParser)
    def get(self, classTypesId: int):
        """
        Retrieve a classTypes using Id
        """
        # authenticate bearer token
        check_admin_return_payload(authenticationParser)

        classTypes = ClasstypeModel.query.get(classTypesId)
        if not classTypes:
            # The classTypes does not exist
            return '', http.client.NOT_FOUND

        return classTypes

    @api.doc('update_classTypes')
    @api.marshal_with(classTypesModel)
    @api.expect(updateParser)
    def put(self, classTypesId: int):
        """
        Update an classTypes, only accessible by a (super) classTypes
        """
        classTypes = (ClasstypeModel.query.filter(
            ClasstypeModel.id == classTypesId).first())
        if not classTypes:
            # The classTypes does not exist
            return '', http.client.NOT_FOUND

        args = updateParser.parse_args()
        payload = authentication_header_parser(args['Authorization'])
        # start by checking if the user is an admin

        check_admin_return_payload(authenticationParser)

        classTypes.class_name = args['class_name'] or classTypes.class_name
        classTypes.class_description = args[
            'class_description'] or classTypes.class_description

        db.session.add(classTypes)
        db.session.commit()

        return classTypes

    @api.doc('delete_classTypes',
             responses={http.client.NO_CONTENT: 'No content'})
    @api.marshal_with(classTypesModel)
    @api.expect(authenticationParser)
    def delete(self, classTypesId: int):
        """
        Delete an classTypes, only accessible by super classTypes
        """
        # authenticate bearer token
        check_admin_return_payload(authenticationParser, super=True)

        classTypes = ClasstypeModel.query.get(classTypesId)
        if not classTypes:
            # The classTypes does not exist
            return '', http.client.NO_CONTENT

        db.session.delete(classTypes)
        db.session.commit()

        return '', http.client.NO_CONTENT


@api.route('/stat/sumquery/')
class ClasstypeSummaryQuery(Resource):
    @api.doc('query count in db: total count')
    @api.expect(authenticationParser)
    def get(self):
        """
        Help find total records in database
        """
        args = authenticationParser.parse_args()
        authentication_header_parser(args['Authorization'])

        classTypes = (ClasstypeModel.query.count())
        return classTypes


@api.route('/stat/datequery/')
class ClasstypeDateQuery(Resource):
    @api.doc('query count in db: daily')
    @api.expect(dateQuery_parser)
    def get(self):
        """
        Help find the daily classtypes created within a range of dates
        """
        args = dateQuery_parser.parse_args()
        authentication_header_parser(args['Authorization'])

        start_date_str = args['startdate']
        end_date_str = args['enddate']

        start_date = datetime.strptime(start_date_str, "%d/%m/%Y").date()
        end_date = datetime.strptime(end_date_str, "%d/%m/%Y").date()

        result = {}

        if start_date > end_date:
            return '', http.client.BAD_REQUEST

        while start_date <= end_date:
            classTypes = (db.session.query(func.count(
                ClasstypeModel.id)).filter(
                    func.date(ClasstypeModel.timestamp) == start_date).all())
            date = start_date.strftime("%d/%m/%Y")
            result[date] = classTypes[0][0]

            start_date = start_date + timedelta(days=1)

        return result


@api.route('/stat/monthquery/')
class ClasstypeMonthQuery(Resource):
    @api.doc('query count in db: monthly')
    @api.expect(monthQuery_parser)
    def get(self):
        """
        Help find the daily classtypes created within a range of month
        """
        args = monthQuery_parser.parse_args()
        authentication_header_parser(args['Authorization'])

        str_year = args['year']
        try:
            year = int(str_year)
        except ValueError:
            return '', http.client.BAD_REQUEST

        result = {}

        if year < 2020:
            return '', http.client.BAD_REQUEST

        for month in range(1, 13):
            classTypes = (db.session.query(func.count(
                ClasstypeModel.id)).filter(
                    func.extract('year', ClasstypeModel.timestamp) ==
                    year).filter(
                        func.extract('month', ClasstypeModel.timestamp) ==
                        month).all())

            result[f'{month}'] = classTypes[0][0]

        return result
