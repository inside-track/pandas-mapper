# pd-mapper

Goals:
* To remove PdMapper from Pemi
* Simplify PdMapper interface
* More flexible handlers
* Contribute to Pandas ecosystem

Idea:
* I want to be able to be able to apply a list of maps to a pandas dataframe
* Each map contains a 0-many sources, 0-many targets and a single transform
* Return a mapped object (ala GroupBy object), which you can use to get the resultant dataframe and errors set


## Initial Dev Setup

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
