# Pydantic Spotlight

## Purpose
pydantic is primarily a parsing library, not a validation library. Validation is a means to an end: building a model which conforms to the types and constraints provided. In other words, pydantic guarantees the types and constraints of the output model, not the input data.

## Characteristic
- **construct()** - allows models to be created without validation this can be useful when data has already been validated or comes from a trusted source and you want to create a model as efficiently as possible (construct() is generally around 30x faster than creating a model with full validation)
- **field ording** - officially, they recommend adding type annotations to all fields because validation is performed in the order fields are defined; fields validators can access the values of earlier fields, but not later ones, this is due to limitations of python. We can use `__fields__.keys()` to ascertain the current field order.
- **... (ellipsis)** - use ellipsis if that field is required even the value is None, which is allowed.
- **PrivateAttr** - when you need to vary or manipulate internal attributes on instances of the model. Private attribute names must start with underscore to prevent conflicts with model fields: both `_attr` and `__attr__` are supported. Noted that `__slots__` filled with private attributes if the object is created by pydantic.
- **parse_obj_as** - a standalone utility function works with arbitrary pydantic-compatible types. This is especially useful when you want to parse results into a type that is not a direct subclass of BaseModel.
- **validator** - customized validation, can be used by decorator. Noted that the function decorated by this validator, should be a class method. If **pre** is set up to True, that validator will be called prior to other validation. If **each_item** is True, the value passes into the validation will be an individual element if the target field is a collection type, e.g. List, Dict, Set etc.
- **schema_extra** - It's also possible to extend/override the generated JSON schema in a model. To do it, use the Config sub-class attribute `schema_extra`.