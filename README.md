# pandas-mapper

The pandas-mapper provides a concise syntax for applying mapping
transformations to [Pandas](http://pandas.pydata.org/) Dataframes
commonly required for ETL workflows.  Possibly the biggest benefit to
using pandas-mapper over the native
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

```
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

A stupidly-simple translation method might be

```
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

```
    mapper = df.mapping([('num', 'translated', translate)])
    translated_df = mapper.mapped
```

The first argument of the mapping method is a list of tuples, where
the first element of the tuple is the source field(s), the second element
is the target field(s), and the (optional) third element is the
transform.

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

then we get two dataframes, one with all of the translated records, and another with the
error records.


## Mapping cardinalities

TODO: redo the stuff in the class docs.

## Contributor Setup

Download and install the [docker community edition](https://www.docker.com/)
that is appropriate for your host os.

We use [invoke](http://www.pyinvoke.org/) to setup and control the environment
for developing, testing, and executing oa-tabcmdr.  This will require that you install
invoke in your host OS.  You may be able to get away with just running
`pip install invoke`.  However, the recommended method is to download and install
[miniconda](https://conda.io/miniconda.html).  Then, create an oa-tabcmdr specific
environment and install invoke in this environment:

```
conda create --name pandas-mapper python=3.6
source activate pandas-mapper
pip install invoke
```

**Note**: if you use miniconda, you will have to run `source activate pandas-mapper`
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
