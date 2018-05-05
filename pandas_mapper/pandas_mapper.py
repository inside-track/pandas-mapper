import pandas as pd


# map - source, target, transform, handler
# mapper - collection of maps, executes maps, directs to targets based on handler
# handler - executes transform, associates result with an output


# Are there really any use cases where I would want to send to multiple targets?
#   or is it just main vs errors?



class Handler:
    def __init__(self):
        self.outputs = {
            'main': {
                'include': 'all',
                'indices': []
            }
        }


    def apply(self, transform, arg, idx):
        # returns the result of the application of a function on an argument
        # arg can be either a value or a pandas series
        # idx is the pandas index

        # or maybe this should return an index, target(s), and values?
        # and then the mapper collates all of the targets using the indecies?
        return [('main', transform(arg), idx)]


class ExcludeHandler(Handler):
    def __init__(self):
        super().__init__()

        self.outputs['errors'] = {
            'include': 'any',
            'indices': []
        }

    def apply(self, transform, arg, idx):
        try:
            return [('main', transform(arg), idx)]
        except Exception as err:
            return [('errors', (arg, err), idx)]

class RecodeHandler(Handler):
    def __init__(self, fun):
        super().__init__()

        self.outputs['errors'] = {
            'include': 'any',
            'indices': []
        }

        self.fun = fun

    def apply(self, transform, arg, idx):
        try:
            return [('main', transform(arg), idx)]
        except Exception as err:
            return [
                ('main', self.fun(arg), idx),
                ('errors', (arg, err), idx)
            ]


class PdMap:
    def __init__(self, source=None, target=None, transform=None, handler=None):
        if isinstance(source, str):
            self.sources = [source]
        else:
            self.sources = list(source or [])

        if isinstance(target, str):
            self.targets = [target]
        else:
            self.targets = list(target or [])

        self.transform = transform
        self.handler = handler or Handler()

        if len(self.sources) == 1 and len(self.targets) == 1 and self.transform is None:
            self._apply = getattr(self, '_apply_copy')
        elif len(self.sources) == 1 and len(self.targets) == 1:
            self._apply = getattr(self, '_apply_one_to_one')
        elif len(self.sources) == 1 and len(self.targets) == 0:
            self._apply = getattr(self, '_apply_one_to_zero')
        elif len(self.sources) == 0 and len(self.targets) == 1:
            self._apply = getattr(self, '_apply_zero_to_one')
        elif len(self.targets) == 1:
            self._apply = getattr(self, '_apply_many_to_one')
        else:
            self._apply = getattr(self, '_apply_many_to_many')

    def _transform(self, arg):
        return self.transform(arg)

    def _transform_one_to_one(self, row):
        return self.handler.apply(self._transform, row[self.sources[0]], row.name)

    def _transform_zero_to_one(self, row):
        return self.handler.apply(self._transform, row['__none__'], row.name)

    def _transform_many_to_one(self, row):
        return self.handler.apply(self._transform, row, row.name)

    def _transform_many_to_many(self, row):
        return self.handler.apply(self._transform, row, row.name)


    def apply(self, source_df, target_df):
        for source in self.sources:
            if source not in source_df:
                raise MissingSourceFieldError('"{}" field not in source dataframe'.format(source))

        return self._apply(source_df)
        # for target in self.targets:
        #     target_df[target] = self._apply(source_df)

        # if len(self.source_df) > 0:
        #     self._apply(source_df)
        # else:
        #     for target in self.targets:
        #         self.mapped_df[target] = None


    # need a better shortcut for copies
    def _apply_copy(self, source_df):
        self.transform = lambda v: v
        return self._apply_one_to_one(source_df)
#        return source_df[self.sources[0]].copy()

    def _apply_one_to_one(self, source_df):
        return source_df[self.sources].apply(
            self._transform_one_to_one, axis=1
        )

    def _apply_many_to_many(self, source_df):
        return source_df[self.sources].apply(self._transform_many_to_many, axis=1).iloc[:,0]



# hmmmmm.... so, if one of the transforms has an error, I want to have a handler that can'
# exclude the entire record
