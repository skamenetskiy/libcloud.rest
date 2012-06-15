# -*- coding:utf-8 -*-
import inspect
from itertools import chain

from libcloud_rest.exception import ValidationError, MissingArguments,\
    UnknownArgument
from libcloud_rest.api.parser import get_method_requirements


__all__ = [
    'validate_header_arguments',
    ]


def validate_driver_arguments(Driver, arguments):
    """
    Validate that in all required arguments are existing.
    @param required_arguments:
    @param arguments:

    @raise: L{MissingHeaderError}
    """
    try:
        required_args = get_method_requirements(Driver.__init__)
        method_with_docstring = Driver.__init__
    except NotImplementedError:
        required_args = get_method_requirements(Driver.__new__)
        method_with_docstring = Driver.__init__
    #required args validate
    missing_args = []
    for arg_altertives in required_args:
        if not any([arg in arguments for arg in arg_altertives]):
            missing_args.append(arg_altertives)
    if missing_args:
        raise MissingArguments(missing_args)
    #optional args validate
    method_args_spec = inspect.getargspec(method_with_docstring)
    method_args = method_args_spec[0][1:]  # with removing 'self' or 'cls' arg
    if method_args_spec[2]:
        pass  # TODO: add docs parsing for keyword arguments
    unknown_arguments = []
    required_args_flat = list(chain(*required_args))
    for arg in arguments:
        if not (arg in method_args or arg in required_args_flat):
            unknown_arguments.append(arg)
    if unknown_arguments:
        raise UnknownArgument(arguments=unknown_arguments)
    return True


class BaseValidator(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.required = kwargs.pop('required', True)

    def __call__(self, data):
        """
        Validate data
        @return True if data correct
        """
        self.raw_data = data
        self._validate()
        return True

    def _validate(self):
        if not self.required and not self.raw_data:
            return True
        self._check_data()

    def _check_data(self):
        """
        Validation function that does not check required flag.
        """
        raise NotImplemented('To use this class inherit from it '
                             'and define _check_data method')


class IntegerValidator(BaseValidator):
    def __init__(self, *args, **kwargs):
        self.max = kwargs.pop('max', None)
        self.min = kwargs.pop('min', None)
        super(IntegerValidator, self).__init__(args, kwargs)

    def _check_data(self):
        try:
            i = int(self.raw_data)
        except (ValueError, TypeError):
            raise ValidationError('Data must be integer')
        if self.max is not None and i > self.max:
            raise ValidationError('Data must be smaller than %i' % self.max)
        if self.max is not None and i < self.min:
            raise ValidationError('Data must be larger than %i' % self.min)


class StringValidator(BaseValidator):
    def _check_data(self):
        if not isinstance(self.raw_data, basestring):
            raise ValidationError('Data must be string')


class DictValidator(BaseValidator):

    def __init__(self, *args, **kwargs):
        if not isinstance(args[0], dict):
            raise TypeError('Argument must be dict')
        self.items_validators = args[0]
        super(DictValidator, self).__init__(args, kwargs)

    def _check_data(self):
        if not isinstance(self.raw_data, dict):
            raise ValidationError('Data must be dict')
        for key, validator in self.items_validators.iteritems():
            validator(self.raw_data.get(key, None))
