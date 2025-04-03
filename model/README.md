# model

- `data_filter.py`: Perform the first two steps of filtering on the source data we mentioned in RQ4.
- `linkProject.py` && linkCode.py: Correlate the source data on Gitcoin with the data on Github, and the results are in internalCsv.
- `encoder.py`: Type variables are processed and one-hot encoded.
- `model.csv`: This file contains the processed data, ready for direct use in `model.R`.
- `model.R`: Perform correlation analysis and redundancy analysis, construct the GLM model, and evaluate its performance. Use `Rscript.exe model.R` to execute.

- `model_cor&redun_anlysis.txt`: The result of correlation analysis and redundancy analysis.
- `model_summarys`: The model summary of bootstrap models.
- `model_summary.txt`: The model summary and evaluation of the original GLM model.