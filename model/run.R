library(mgcv)
library(carData)
library(corrplot)
library(car)
library(rms)
library(Hmisc)
library(boot)

if (!dir.exists("model_summarys")) {
    dir.create("model_summarys")
}

df <- read.csv("data.csv")

df$code_smells[is.na(df$code_smells)] <- 0
df$ncloc[is.na(df$ncloc)] <- 0
df$complexity[is.na(df$complexity)] <- 0

df$code_smells_log <- log(df$code_smells + 1)
df$ncloc_log <- log(df$ncloc + 1)
df$complexity_log <- log(df$complexity + 1)

response_var <- "value_in_usdt"
df$value_in_usdt_log <- log(df[[response_var]] + 1)
response_var_log <- "value_in_usdt_log"


var_list <- c(
    'project_length_Hours', 'project_length_Days',
    'project_length_Weeks', 
    "bounty_type_Bug", "bounty_type_Code_Review", "bounty_type_Design", 
    "bounty_type_Documentation", "bounty_type_Feature", "bounty_type_Improvement",
    "bounty_type_Other", "bounty_type_Project", "bounty_type_Security", 
    "issue_timeout", "experience_level_Beginner", 'experience_level_Advanced', 
    'experience_level_Intermediate', 'repo_forks_count',
    "repo_language_JavaScript", "repo_language_TypeScript", 'repo_language_Others',
    'repo_stargazers_count', 'repo_open_issues_count',
    'code_additions', 'code_deletions',
    'code_changed_files', 'code_finish_time', 'issue_len_description',
    'fulfillments_len', 'bounty_num', 'bounty_change_num',
    'code_smells_log', 'ncloc_log'
    , 'complexity_log'
)


df_sub <- df[, var_list]
df_sub <- as.data.frame(lapply(df_sub, as.numeric))


correlation_matrix <- cor(df_sub, method = "spearman", use = "complete.obs")
capture.output(correlation_matrix, file = "model_correlation.txt")


high_cor_vars <- which(abs(correlation_matrix) > 0.7, arr.ind = TRUE)
high_cor_vars <- high_cor_vars[high_cor_vars[,1] != high_cor_vars[,2], ]

high_cor_groups <- list()
if (nrow(high_cor_vars) > 0) {
    for (i in 1:nrow(high_cor_vars)) {
        var1 <- rownames(correlation_matrix)[high_cor_vars[i, 1]]
        var2 <- colnames(correlation_matrix)[high_cor_vars[i, 2]]
        
        found <- FALSE
        for (j in seq_along(high_cor_groups)) {
            if (var1 %in% high_cor_groups[[j]] || var2 %in% high_cor_groups[[j]]) {
                high_cor_groups[[j]] <- unique(c(high_cor_groups[[j]], var1, var2))
                found <- TRUE
                break
            }
        }
        if (!found) {
            high_cor_groups[[length(high_cor_groups) + 1]] <- c(var1, var2)
        }
    }
}

set.seed(1000) 
remove_vars_cor <- c()
for (group in high_cor_groups) {
    keep_var <- sample(group, 1) 
    remove_vars_cor <- c(remove_vars_cor, setdiff(group, keep_var)) 
}


capture.output('Spearman Delete:', file = "model_correlation.txt", append=TRUE)
capture.output(unique(remove_vars_cor), file = "model_correlation.txt", append=TRUE)
selected_vars_cor <- setdiff(var_list, unique(remove_vars_cor))
capture.output('Spearman Save:', file = "model_correlation.txt", append=TRUE)
capture.output(selected_vars_cor, file = "model_correlation.txt", append=TRUE)


png("Hierarchical.png", width = 800, height = 600)
corrplot(correlation_matrix, method = "circle", type = "upper",
          tl.col = "black", tl.cex = 0.7, diag = FALSE)
dev.off()



df_sub_redun <- df[, selected_vars_cor]
df_sub_redun <- as.data.frame(lapply(df_sub_redun, as.numeric))
dd <- datadist(df_sub_redun)
options(datadist = "dd")


redun_result <- redun(~ ., 
                      data = df_sub_redun,
                      nk = 0, 
                      r2 = 0.9)


capture.output('Redundant Results:', file = "model_correlation.txt", append=TRUE)
capture.output(redun_result, file = "model_correlation.txt", append=TRUE)


final_vars <- setdiff(selected_vars_cor, redun_result$Out)
capture.output('Final Save Variables:', file = "model_correlation.txt", append=TRUE)
capture.output(final_vars, file = "model_correlation.txt", append=TRUE)


gam_formula <- as.formula(paste(response_var_log, "~", paste(final_vars, collapse = " + ")))
original_model <- glm(gam_formula, data = df, family = gaussian)
original_summary <- summary(original_model)
null_model <- glm(as.formula(paste(response_var_log, "~ 1")), data = df, family = gaussian)
original_r2 <- 1 - (original_model$deviance / null_model$deviance)


n_obs <- nrow(df)


n_boot <- 1000
optimism_values <- numeric(n_boot)


pb <- txtProgressBar(min = 0, max = n_boot, style = 3)


for (i in 1:n_boot) {
    tryCatch({
        boot_indices <- sample(n_obs, size = n_obs, replace = TRUE)
        boot_data <- df[boot_indices, ]


        boot_model <- glm(gam_formula, data = boot_data, family = gaussian)
        
        boot_null_model <- glm(as.formula(paste(response_var_log, "~ 1")), data = boot_data, family = gaussian)
        boot_r2 <- 1 - (boot_model$deviance / boot_null_model$deviance)

        
        pred_orig <- predict(boot_model, newdata = df)
        

        ss_total <- sum((df[[response_var_log]] - mean(df[[response_var_log]]))^2, na.rm = TRUE)
        ss_residual <- sum((df[[response_var_log]] - pred_orig)^2, na.rm = TRUE)
        r2_orig <- 1 - (ss_residual / ss_total)
        
        optimism_values[i] <- boot_r2 - r2_orig
        
        
        capture.output(
            cat("=== Bootstrap Iteration", i, "===\n"),
            print(summary(boot_model)),
            cat("\nBootstrap R²:", boot_r2),
            cat("\nOriginal Data R²:", r2_orig),
            cat("\nOptimism:", optimism_values[i]),
            file = paste0("model_summarys/model_", sprintf("%04d", i), ".txt"))
    }, error = function(e) {
        message("Error in iteration ", i, ": ", conditionMessage(e))
    })
    
    
    setTxtProgressBar(pb, i)
}
close(pb)


average_optimism <- mean(optimism_values, na.rm = TRUE)
adjusted_r2 <- original_r2 - average_optimism


capture.output(
    cat("=== Final Model Summary (GLM with Log-Transformed Y) ===\n"),
    print(summary(original_model)),
    cat("\n\n=== Bootstrap Validation Results ===\n"),
    cat("Original R²:", original_r2, "\n"),
    cat("Average Optimism:", average_optimism, "\n"),
    cat("Optimism-Adjusted R²:", adjusted_r2, "\n"),
    cat("Number of Successful Bootstraps:", sum(!is.na(optimism_values)), "\n"),
    file = "model_summary.txt"
)

cat("\n=== Final Results (GLM with Log-Transformed Y) ===")
cat("\nOriginal R²:", original_r2)
cat("\nAverage Optimism:", average_optimism)
cat("\nOptimism-Adjusted R²:", adjusted_r2)
cat("\nResults saved to: model_summary.txt")