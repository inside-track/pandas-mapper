# pandas-mapper

The pandas-mapper is a Python pacckage that provides a concise syntax
for applying mapping transformations to
[Pandas](http://pandas.pydata.org/) Dataframes commonly required for
ETL workflows.  Possibly the biggest benefit to using pandas-mapper
over the native
[pandas.Dataframe.apply](http://pandas.pydata.org/pandas-docs/version/0.22/generated/pandas.DataFrame.apply.html)
method is a robust error handling mechanism.  Instead of raising an
error, mapping errors can be redirected to an errors Dataframe, which
can then be handled by the user as needed.


## Getting started

To get started, install pandas-mapper in your project using pip

```
pip install pandas-mapper
```

and then use it your project by importing the package

```
import pandas_mapper
```

When you import this package in your project, it adds the `mapping` method to Pandas dataframe
objects.  Suppose you had a dataframe containing integers and the English word for the integer
and you want to translate the names to Spanish.

```python
import pandas as pd
import pandas_mapper

df = pd.DataFrame(
    {
        'num': [1, 2, 3],
        'name': ['one', 'two', 'three'],
        'num_name': ['1-one', '2-two', '3-three']
    }
)

```

| num | name  | num_name |
| -   | -     | -        |
| 1   | one   | 1-one    |
| 2   | two   | 2-two    |
| 3   | three | 3-three  |


A stupidly-simple translation method might be

```python
def translate(val):
    if val == 1:
        return 'uno'
    elif val == 2:
        return 'dos'
    elif val == 3:
        return 'tres'
    else:
        raise ValueError('Unknown translation: {}'.format(val))
```

The translation can be accomplished using pandas-mapper via

```python
mapper = df.mapping([('num', 'translated', translate)])
translated_df = mapper.mapped
```

The first argument of the mapping method is a list of tuples, where
the first element of the tuple is the source column(s), the second element
is the target column(s), and the (optional) third element is the
transform.  In this example, we only have one map in the list, so the result is
a dataframe with a single column:

| translated |
| -          |
| uno        |
| dos        |
| tres       |



## Handling errors

Our stupidly-simple translation will raise an error if we supply it with the number `4`.  Suppose
we added another record with the number `4` to our `df` defined above.  If we apply the same
mapping as above, pandas-mapper will raise a `ValueError`.  However, if we supply the `mapping`
method with the `on_error='redirect'` option via

```
mapper = df.mapping([('num', 'translated', translate)], on_error='redirect')
translated_df = mapper.mapped
translation_errors_df = mapper.errors
```

then we get two dataframes, one with the translated records (`mapper.mapped`):

| translated |
| -          |
| uno        |
| dos        |
| tres       |

and another with the error records (`mapper.errors`):

| num | name  | num_name | __errror__                                        |
| -   | -     | -        | -                                                 |
| 4   | four  | 4-four   | {'msg': 'ValueError(4): Unknown translation: 4... |


## Mapping cardinalities

Each map can be defined with 0 or more sources, 0 or more targets, and
0 or 1 transform functions.  The expected arguments and return values of the
transform function is depenedent on the number of source and target columns used.

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

### Examples

#### Zero-to-one

Zero-to-one mappings can be used to set a column to a constant:

```python
df.mapping([None, 'five', transform=5])
```

Or defined by some function that generates output:

```python
import random
df.mapping([(None, 'rando', random.random)]).mapped
```

#### One-to-one
Our translation function defined above is an example of a one-to-one transform:

```python
df.mapping([('num', 'translated', translate)])
```

#### Many-to-one
Concatenation is an example of a many-to-one operation:

```python
df.mapping([(['num', 'name'], 'num-name', lambda row: '-'.join(row.apply(str)))])
```

#### Many-to-Many
Deconcatenation is an example of a one-to-many operation.  One-to-many operations
require the same method signature as many-to-many:

```python
def deconcatenate(row):
    split_values = row['num_name'].split('-')
    row[num'] = split_values[0]
    row[name'] = split_values[1]
    return row

df.mapping([('num_name', ['num', 'name'], deconcatenate)])
```


## Other options

The mapping method also supports an `inplace` option, which is `False` by default.  This
will modify the dataframe in place, bringing along all columns that it started with.  For example:

```python
df.mapping([('num', 'translated', translate)], inplace=True).mapped
```

| num | name  | num_name | translated |
| -   | -     | -        | -          |
| 1   | one   | 1-one    | uno        |
| 2   | two   | 2-two    | dos        |
| 3   | three | 3-three  | tres       |

Modifying the dataframe inplace can be useful when you need to chain together transformations,
like when the output of one map in needed as the input for another map.

## Contributor Setup

Download and install the [docker community edition](https://www.docker.com/)
that is appropriate for your host os.

We use [invoke](http://www.pyinvoke.org/) to setup and control the environment
for developing and testing this project.  This will require that you install
invoke in your host OS.  You may be able to get away with just running
`pip install invoke`.  However, the recommended method is to download and install
[miniconda](https://conda.io/miniconda.html).  Then, create a project-specific
environment and install invoke in this environment:

```
conda create --name pandas-mapper python=3.6
conda activate pandas-mapper
pip install invoke
```

**Note**: if you use miniconda, you will have to run `conda activate pandas-mapper`
each time you start a new terminal session.

Once invoke is installed, you can build the docker containers to use the dev/test environment

```
inv build
```

Spin up the dev/test environment via

```
inv up --jupyter-port=8892
```

Run the test suite via

```
inv test
```
