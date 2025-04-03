# Understanding the Incentive Mechanism of Bounty Issues in Open Source Communities

## Directory Structure

```shell
├─characteristics
├─detector
├─model
│  ├─internalCsv
│  └─modelSummarys
├─motivation
│  ├─commits
│  │  ├─commitImages
│  │  ├─internalCsv
│  │  └─repoCommits
│  └─issues
│      ├─internalCsv
│      └─issueImages
├─rawData
└─survey
```

## Content navigation

- **survey:** Response information received from the survey we issued.
- **rawData:** Source data on Gitcoin and data set statistics related information.
- **motivation:** Statistical result in RQ1.
- **characteristics:** Statistical result in RQ2 and RQ3.
- **model:** The GAM model we established in RQ4.
- **detector:** The detector we constructed in RQ5.

**Note**: Each folder contains a README.md file to guide you through its contents.

## Dependencies

**Pip packages:**

```python
dependencies = [
    "json",
    "pandas",
    "matplotlib.pyplot",
    "matplotlib.rcParams",
    "sklearn.preprocessing",
    "sklearn.model_selection",
    "sklearn.svm",
    "sklearn.naive_bayes",
    "sklearn.neighbors",
    "sklearn.ensemble",
    "sklearn.tree",
    "sklearn.metrics",
    "xgboost",
    "requests",
    "urllib3",
    "datetime",
    "dateutil.parser",
    "os",
    "tqdm",
    "logging",
    "ast",
    "seaborn",
    "scipy.stats.mannwhitneyu",
    "numpy"
]
```

**R packages:**

```R
dependencies <- c(
    "mgcv",
    "carData",
    "corrplot",
    "car",
    "rms",
    "Hmisc",
    "boot"
)
```

