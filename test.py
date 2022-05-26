from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, PrivateAttr, ValidationError, parse_obj_as


object_setattr = object.__setattr__

def construct_test():

    class Model(BaseModel):
        name: str
        age: int

        @classmethod
        def construct(cls,  _fields_set = None, **values):
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
            object_setattr(m, '__dict__', fields_values) # set up all the values in __dict__ without validation, which will set value to respective field by dict key.
            if _fields_set is None:
                _fields_set = set(values.keys())
            object_setattr(m, '__fields_set__', _fields_set)
            m._init_private_attributes() # init default value if the model has PrivateAttr on fields
            return m

    data = {'name':'python', 'age':15}
    model = Model.construct(**data)
    assert 'python' == model.name
    assert 15 == model.age

    # please use construct carefully because the default behavior won't validate the type and value even the filed doesn't exist like the following
    data = {'name':'python', 'age':15, 'star': 5}
    model = Model.construct(**data)
    assert 5 == model.star # star isn't existing in model


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
    assert not list(filter(lambda attr: attr not in ['_a', '__b__'], model.__slots__))  # not include _c

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

    my_data = [{'name':'python', 'age':15}, {'name':'java', 'age':20}]
    models = parse_obj_as(List[Model], my_data)
    
    assert 2 == len(models)
    assert 'python' == models[0].name
    assert 15 == models[0].age
    assert 'java' == models[1].name
    assert 20 == models[1].age


if __name__ == '__main__':
    construct_test()
    field_ordering_test()
    ellipsis_test()
    private_attr_test()
    parse_obj_as_test()
