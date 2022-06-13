from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, PrivateAttr, ValidationError, parse_obj_as, validator


def construct_test():

    object_setattr = object.__setattr__

    class Model(BaseModel):
        name: str
        age: int

        @classmethod
        def construct(cls,  _fields_set=None, **values):
            """
            copy from https://github.com/samuelcolvin/pydantic/blob/abea8232eef0eeeb728824cdec9b445dfbd3192e/pydantic/main.py#L581
            """
            m = cls.__new__(cls)
            fields_values: Dict[str, Any] = {}
            for name, field in cls.__fields__.items():
                if name in values:
                    fields_values[name] = values[name]
                elif not field.required:
                    fields_values[name] = field.get_default()
            fields_values.update(values)
            # set up all the values in __dict__ without validation, which will set value to respective field by dict key.
            object_setattr(m, '__dict__', fields_values)
            if _fields_set is None:
                _fields_set = set(values.keys())
            object_setattr(m, '__fields_set__', _fields_set)
            # init default value if the model has PrivateAttr on fields
            m._init_private_attributes()
            return m

    data = {'name': 'python', 'age': 15}
    model = Model.construct(**data)
    assert 'python' == model.name
    assert 15 == model.age

    # please use construct carefully because the default behavior won't validate the type and value even the filed doesn't exist like the following
    data = {'name': 'python', 'age': 15, 'star': 5}
    model = Model.construct(**data)
    assert 5 == model.star  # star isn't existing in model

    trace_list = []

    class Demo:
        """Normal Case
        The way python constructs objects will invoke __new__ frist, followed by __init__
        """
        def __new__(cls, *args):
            trace_list.append('new')
            return object.__new__(cls)

        def __init__(self):
            trace_list.append('init')

    Demo()
    assert ['new', 'init'] == trace_list


def field_ordering_test():
    class Model(BaseModel):
        a: int
        b = 2
        c: int = 1
        d = 0
        e: float

    assert 5 == len(Model.__fields__.keys())
    assert ['a', 'c', 'e', 'b', 'd'] == list(Model.__fields__.keys())


def ellipsis_test():
    class Model(BaseModel):
        a: Optional[int]
        b: Optional[int] = ...
        c: Optional[int] = Field(...)

    model = Model(b=None, c=1)
    assert None == model.a
    assert None == model.b
    assert 1 == model.c

    try:
        model = Model(a=1)
    except ValidationError as e:
        assert 2 == len(e.raw_errors)
        assert 'b' == e.raw_errors[0]._loc
        assert 'field required' == e.raw_errors[0].exc.msg_template
        assert 'c' == e.raw_errors[1]._loc
        assert 'field required' == e.raw_errors[1].exc.msg_template


def private_attr_test():
    class Model(BaseModel):
        _a: str = PrivateAttr(default='pydantic')
        __b__: int = PrivateAttr(default=None)
        _c: list  # not required
        d: set  # required, because the filed name doesn't start with an underscore

    model = Model(d=set())
    assert not list(filter(lambda attr: attr not in [
                    '_a', '__b__'], model.__slots__))  # not include _c

    try:
        model = Model()
    except ValidationError as e:
        assert 1 == len(e.raw_errors)
        assert 'd' == e.raw_errors[0]._loc
        assert 'field required' == e.raw_errors[0].exc.msg_template


def parse_obj_as_test():
    class Model(BaseModel):
        name: str
        age: int

    my_data = [{'name': 'python', 'age': 15}, {'name': 'java', 'age': 20}]
    models = parse_obj_as(List[Model], my_data)

    assert 2 == len(models)
    assert 'python' == models[0].name
    assert 15 == models[0].age
    assert 'java' == models[1].name
    assert 20 == models[1].age


def validator_test():
    class Model(BaseModel):
        score_records: List[int]
        name_records: List[str]

        # pre is True force the execute the map function before validating fields
        @validator('*', pre=True)
        def split_str(cls, v):
            if isinstance(v, str):
                return v.split(',')
            return v

        # fetch each item in a list in this case
        @validator('score_records', each_item=True)
        def check_score(cls, v):
            if v < 0:
                raise ValueError(f'score shouldn\'t be less than 0, {v}')
            return v

    model = Model(name_records='A,B,C', score_records='1,2,3')
    assert ['A', 'B', 'C'] == model.name_records
    assert [1, 2, 3] == model.score_records

    model = Model(name_records=['D', 'E', 'F'], score_records=[4, 5, 6])
    assert ['D', 'E', 'F'] == model.name_records
    assert [4, 5, 6] == model.score_records

    try:
        Model(name_records=['G', 'H', 'I'], score_records=[1, 0, 2, -1])
    except ValueError as e:
        assert [{'loc': ('score_records', 3), 'msg': "score shouldn't be less than 0, -1",
                 'type': 'value_error'}] == e.errors()
        # loc: (field_name, index)


def config_test():
    class Model(BaseModel):
        name: str
        age: int

        class Config:
            schema_extra = {
                'example': {
                    'name': 'python',
                    'age': 15
                }
            }
            
    schema = Model.schema().get('example', None)
    """
    {
        "title":"Model",
        "type":"object",
        "properties":{
            "name":{
                "title":"Name",
                "type":"string"
            },
            "age":{
                "title":"Age",
                "type":"integer"
            }
        },
        "required":[
            "name",
            "age"
        ],
        "example":{
            "name":"python",
            "age":15
        }
    }
    """

    assert 'python' == schema.get('name', None)
    assert 15 == schema.get('age', None)


if __name__ == '__main__':
    construct_test()
    field_ordering_test()
    ellipsis_test()
    private_attr_test()
    parse_obj_as_test()
    validator_test()
    config_test()
