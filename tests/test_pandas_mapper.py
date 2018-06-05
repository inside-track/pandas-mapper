import pytest

import pandas as pd

from pandas.testing import assert_frame_equal

import pandas_mapper

from pandas_mapper.pandas_mapper import MissingSourceFieldError
from pandas_mapper.pandas_mapper import PdMappingError

def translate(val):
    if val == 1:
        return 'uno'
    elif val == 2:
        return 'dos'
    elif val == 3:
        return 'tres'
    else:
        raise ValueError('Unknown translation: {}'.format(val))

def concatenate(delim=''):
    def _concatenate(row):
        return delim.join(list(row.apply(str)))
    return _concatenate

def deconcatenate(row):
    split_values = row['num_name'].split('-')
    row['split_num'] = split_values[0]
    row['split_name'] = split_values[1]
    return row




class TestBasic:

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            {
                'num': [1, 2, 3],
                'name': ['one', 'two', 'three'],
                'num_name': ['1-one', '2-two', '3-three']
            }
        )

    @pytest.fixture
    def df_translate_err(self):
        return pd.DataFrame(
            {
                'num': [1, 2, 3, 4],
                'name': ['one', 'two', 'three', 'four'],
                'num_name': ['1-one', '2-two', '3-three', '4-four']
            }
        )

    def test_one_to_one_map(self, df):
        '''
        One-to-one mapping
        '''

        mapper = df.mapping([('num', 'translated', translate)])

        actual_df = mapper.mapped
        expected_df = pd.DataFrame({'translated': ['uno', 'dos', 'tres']})

        assert_frame_equal(actual_df, expected_df)

    def test_many_to_one_map(self, df):
        '''
        Many-to-one mapping
        '''

        mapper = df.mapping([(['name', 'num'], 'concatenated', concatenate('-'))])

        actual_df = mapper.mapped
        expected_df = pd.DataFrame({'concatenated': ['one-1', 'two-2', 'three-3']})

        assert_frame_equal(actual_df, expected_df)

    def test_many_to_one_map_empty(self):
        '''
        Many-to-one mapping with empty data
        '''
        df = pd.DataFrame(columns=['col1', 'col2'])

        mapper = df.mapping([(['col1', 'col2'], 'col3', lambda row: row['col2'])])

        actual_df = mapper.mapped
        expected_df = pd.DataFrame(columns=['col3'])

        assert_frame_equal(actual_df, expected_df, check_dtype=False)

    def test_one_to_many_map(self, df):
        '''
        One-to-many mapping
        '''

        mapper = df.mapping([('num_name', ['split_name', 'split_num'], deconcatenate)])

        actual_df = mapper.mapped
        expected_df = pd.DataFrame({
            'split_name': ['one', 'two', 'three'],
            'split_num': ['1', '2', '3'],
        })

        assert_frame_equal(actual_df, expected_df)

    def test_multiple_maps(self, df):
        '''
        Multiple mappings of various cardinalities
        '''

        mapper = df.mapping([
            ('num', 'translated', translate),
            (['name', 'num'], 'concatenated', concatenate('-')),
            ('num_name', ['split_name', 'split_num'], deconcatenate)
        ])

        actual_df = mapper.mapped
        expected_df = pd.DataFrame(
            {
                'translated': ['uno', 'dos', 'tres'],
                'concatenated': ['one-1', 'two-2', 'three-3'],
                'split_name': ['one', 'two', 'three'],
                'split_num': ['1', '2', '3']
            },
        )
        assert_frame_equal(actual_df, expected_df)


    def test_alternate_map_style(self, df):
        '''
        You can also use a more verbose mapping style
        '''

        mapper = df.mapping([
            pd.PdMap(source='num', target='translated', transform=translate),
            pd.PdMap(source=['name', 'num'], target='concatenated', transform=concatenate('-')),
            pd.PdMap(source='num_name', target=['split_name', 'split_num'], transform=deconcatenate),
            pd.PdMap(target='five', transform=5)
        ])

        actual_df = mapper.mapped
        expected_df = pd.DataFrame(
            {
                'translated': ['uno', 'dos', 'tres'],
                'concatenated': ['one-1', 'two-2', 'three-3'],
                'split_name': ['one', 'two', 'three'],
                'split_num': ['1', '2', '3'],
                'five': [5, 5, 5]
            },
        )
        assert_frame_equal(actual_df, expected_df)


    def test_one_to_zero_map(self, df):
        '''
        One-to-zero mapping
        '''

        def recorder(values):
            def _recorder(value):
                values.append(value)
            return _recorder

        saved = []
        df.mapping([('num', None, recorder(saved))])

        assert saved == [1, 2, 3]


    def test_many_to_zero_map(self, df):
        '''
        Many-to-zero mapping
        '''

        def recorder(values):
            def _recorder(row):
                values.append('-'.join([str(v) for v in row.values]))
            return _recorder

        saved = []
        df.mapping([(['num', 'name'], None, recorder(saved))])

        assert saved == ['1-one', '2-two', '3-three']


    def test_zero_to_one_map_function(self, df):
        '''
        Zero-to-one mapping with a function
        '''
        mapper = df.mapping([(None, 'my_constant', lambda: 5)])

        actual_df = mapper.mapped
        expected_df = pd.DataFrame({'my_constant': [5, 5, 5]})

        assert_frame_equal(actual_df, expected_df)

    def test_zero_to_one_map_constant(self, df):
        '''
        Zero-to-one mapping with a constant
        '''
        mapper = df.mapping([(None, 'my_constant', 5)])

        actual_df = mapper.mapped
        expected_df = pd.DataFrame({'my_constant': [5, 5, 5]})

        assert_frame_equal(actual_df, expected_df)



    def test_error_w_raise_mode(self, df_translate_err):
        '''
        An error is encountered during mapping and is raised
        '''

        with pytest.raises(PdMappingError):
            df_translate_err.mapping([('num', 'translated', translate)])

    def test_errors_excluded_w_redirect(self, df_translate_err):
        '''
        An error can be redirected to a separate dataframe
        '''

        mapper = df_translate_err.mapping([('num', 'translated', translate)], on_error='redirect')

        actual_df = mapper.mapped
        expected_df = pd.DataFrame({'translated': ['uno', 'dos', 'tres']})

        assert_frame_equal(actual_df, expected_df)

    def test_errors_redirected_w_redirect(self, df_translate_err):
        '''
        An error can be redirected to a separate dataframe
        '''

        mapper = df_translate_err.mapping([('num', 'translated', translate)], on_error='redirect')

        actual_df = mapper.errors
        expected_df = df_translate_err.loc[[3]]

        compare_cols = ['num', 'name', 'num_name']
        assert_frame_equal(actual_df[compare_cols], expected_df[compare_cols])


    def test_errors_column(self, df_translate_err):
        '''
        An error column is generated that contains a dictionary with details of the error
        '''

        mapper = df_translate_err.mapping([('num', 'translated', translate)], on_error='redirect')

        actual_msg = mapper.errors['__error__'].iloc[0]

        expected_msg = {
            'msg': 'ValueError(4): Unknown translation: 4',
            'err': ValueError('Unknown translation: 4',),
            'arg': 4,
            'sources': ['num'],
            'targets': ['translated'],
            'transform': translate
        }
        assert actual_msg['err'].__class__ is ValueError

        del actual_msg['err']
        del expected_msg['err']
        assert actual_msg == expected_msg


    def test_mapping_inplace(self, df):
        '''
        Using inplace=True modified the original dataframe
        '''

        mapper = df.mapping([('num', 'translated', translate)], inplace=True)

        actual_df = mapper.mapped
        expected_addtl_df = pd.DataFrame({'translated': ['uno', 'dos', 'tres']})

        assert_frame_equal(actual_df, df)
        assert_frame_equal(actual_df[['translated']], expected_addtl_df)

    def test_mapping_inplace_chaining(self, df):
        '''
        When inplace is used, maps can be reuse the output of previous maps
        '''

        mapper = df.mapping(
            [
                ('num', 'translated', translate),
                ('translated', 'hola', 'Hola {}'.format)
            ],
            inplace=True
        )

        actual_df = mapper.mapped
        expected_addtl_df = pd.DataFrame({
            'translated': ['uno', 'dos', 'tres'],
            'hola': ['Hola uno', 'Hola dos', 'Hola tres']
        })

        assert_frame_equal(actual_df, df)
        assert_frame_equal(actual_df[['translated', 'hola']], expected_addtl_df)


    def test_missing_fields(self, df):
        '''
        A specific error is raised if a non-existant field is used
        '''

        with pytest.raises(MissingSourceFieldError):
            df.mapping([('numero', 'translated', translate)])
