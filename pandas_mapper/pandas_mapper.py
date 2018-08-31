import logging

import pandas as pd

import pandas_mapper
from pandas_mapper import LOG

class MissingSourceFieldError(Exception): pass
class PdMappingError(Exception): pass

class PdMap:
    def __init__(self, source=None, target=None, transform=None):
        '''Defines how a set of Pandas dataframe columns are to be mapped.

        The expected arguments and return values of the transform
        function need to be compatible with the cardinality of the
        transform:

          * If the mapping has a single source and single target columns, then the
            transform function should accept a single value and return a single value.
          * If the mapping involves multiple source columns, then the
            function should accept a single dict-like object where the
            keys are the names of the source columns.  In this case, if the mapping
            has a single target, then the retun value of the transform function should contain
            a single value.  However, if the mapping has multiple targets, then the return
            value should be the same dict-like object that was passed to the function, with
            the target-column keys of that object have been modified in place by the function.
          * If the mapping has no source columns, then the transform can either be a constant
            (e.g., the integer 5), or a function that accepts no arguments but returns a value
            (which may be useful if you want to use a random number generator).

        Args:
          source (str, list): Contains the name or names of the source (input) columns to use.
          target (str, list): Contains the name or names of the target (output) columns that
                              will be generated.
          transform(func, obj): A function that is used to map the source(s) to the target(s).

        '''

        if isinstance(source, str):
            self.sources = [source]
        else:
            self.sources = list(source or [])

        if isinstance(target, str):
            self.targets = [target]
        else:
            self.targets = list(target or [])

        self.transform = transform

        self.errors = {
            'indices': [],
            'results': []
        }


        if len(self.sources) == 1 and len(self.targets) == 1 and self.transform is None:
            self._apply = getattr(self, '_apply_copy')
        elif len(self.sources) == 1 and len(self.targets) <= 1:
            self._apply = getattr(self, '_apply_one_to_one')
        elif len(self.sources) == 0 and len(self.targets) == 1:
            if callable(self.transform):
                self._apply = getattr(self, '_apply_zero_to_one')
            else:
                self._apply = getattr(self, '_apply_constant')
        elif len(self.targets) == 1:
            self._apply = getattr(self, '_apply_many_to_one')
        else:
            self._apply = getattr(self, '_apply_many_to_many')

    def apply(self, source_df, target_df):
        for source in self.sources:
            if source not in source_df:
                raise MissingSourceFieldError('"{}" field not in the source dataframe'.format(source))

        if len(source_df) > 0:
            applied_df = self._apply(source_df)

            if len(self.targets) == 1:
                target_df[self.targets[0]] = applied_df
            else:
                for target in self.targets:
                    target_df[target] = applied_df[target]
        else:
            for target in self.targets:
                target_df[target] = None

        return self


    def _try_transform(self, arg, idx):
        try:
            result = self.transform(arg)
        except Exception as err:
            result = (arg, err)
            self.errors['indices'].append(idx)
            self.errors['results'].append(result)
        return result


    def _transform_one_to_one(self, row):
        return self._try_transform(row[self.sources[0]], row.name)

    def _transform_zero_to_one(self, row):
        return self._try_transform(row['__none__'], row.name)

    def _transform_many_to_one(self, row):
        return self._try_transform(row, row.name)

    def _transform_many_to_many(self, row):
        return self._try_transform(row, row.name)


    def _apply_copy(self, source_df):
        return source_df[self.sources[0]].copy()

    def _apply_constant(self, source_df):
        return pd.Series([self.transform] * len(source_df), source_df.index)

    def _apply_zero_to_one(self, source_df):
        return pd.Series([self.transform() for i in range(len(source_df))], source_df.index)

    def _apply_one_to_one(self, source_df):
        return source_df[self.sources].apply(self._transform_one_to_one, axis=1)

    def _apply_many_to_one(self, source_df):
        return source_df[self.sources].apply(self._transform_many_to_one, axis=1)

    def _apply_many_to_many(self, source_df):
        return source_df[self.sources].apply(self._transform_many_to_many, axis=1)

class PdMapper:
    def __init__(self, source_df, maps, inplace=False, on_error='raise'):
        '''
        Takes a list of maps, applies them, and redirects any errors.

        Args:
          source_df (pd.DataFrame): The dataframe to apply the mapping to.
          maps (list): A list of tuples or ``PdMap``s that define the mapping.  If a list of
                       tuples is supplied, the 0th element of the tuple is the source field(s),
                       the 1st element is the target field(s), and the (optional) 2nd element is the
                       transform.
          inplace (boolean): If True, do operation inplace.
          on_error (str): 'raise' (default) will raise an error if any mapping errors
                          are encountered.  'redirect' will exclude any error records from the
                          main output (e.g., ``mapped`` attribute) and place them in a
                          dataframe accessible through the ``errors`` attribute.

        Attributes:
          mapped (pd.DataFrame): A dataframe containing the result of the mapping operation.
          errors (pd.DataFrame): A dataframe containing any records excluded from the main
                                 ``mapped`` dataframe when ``on_error='redirect'``.
        '''

        if inplace:
            self.source_df = source_df
            self.mapped = source_df
        else:
            self.source_df = source_df.copy()
            self.mapped = pd.DataFrame(index=self.source_df.index)

        self.maps = self._coerce_maps(maps)
        self.idx_errors = []
        self.errors = pd.DataFrame([])
        self.on_error = on_error

    @staticmethod
    def _coerce_maps(maps):
        coerced = []
        for amap in maps:
            if isinstance(amap, PdMap):
                coerced.append(amap)
            else:
                coerced.append(
                    PdMap(
                        source=amap[0] if len(amap) > 0 else None,
                        target=amap[1] if len(amap) > 1 else None,
                        transform=amap[2] if len(amap) > 2 else None
                    )
                )
        return coerced

    def _collect_errors(self):
        self.idx_errors = [idx for pd_map in self.maps for idx in pd_map.errors['indices']]
        errors = [
            {
                'msg': '{}({}): {}'.format(err[1].__class__.__name__, err[0], err[1]),
                'err': err[1],
                'arg': err[0],
                'sources': pd_map.sources,
                'targets': pd_map.targets,
                'transform': pd_map.transform
            }
            for pd_map in self.maps for err in pd_map.errors['results']
        ]

        self.errors = self.source_df.merge(
            pd.DataFrame({'__error__': errors}, index=self.idx_errors),
            how='inner',
            left_index=True,
            right_index=True
        )

    def _handle_errors(self):
        if len(self.errors) == 0:
            return

        if self.on_error == 'raise':
            for idx, err in self.errors.iterrows():
                LOG.error('Mapping error at index %s: %s', idx, err['__error__'])

            raise PdMappingError(
                'Raising exception due to {} mapping errors. See log for details.'.format(
                    len(self.errors)
                )
            )
        elif self.on_error == 'redirect':
            self.mapped.drop(self.idx_errors, inplace=True)
            self.errors['__error__'].apply(lambda v: LOG.error(v))
        else:
            raise ValueError('unknown on_error supplied: {}'.format(self.on_error))



    def apply(self):
        for pd_map in self.maps:
            pd_map.apply(self.source_df, self.mapped)

        self._collect_errors()
        self._handle_errors()

        return self


# Monkeypatch Pandas for ease of use
def mapping(self, maps, inplace=False, on_error='raise'):
    return PdMapper(self, maps, inplace=inplace, on_error=on_error).apply()

pd.DataFrame.mapping = mapping
pd.PdMap = PdMap
