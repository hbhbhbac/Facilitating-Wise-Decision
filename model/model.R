library(mgcv)
library(carData)
library(corrplot)
library(car)
library(rms)
library(Hmisc)
library(boot)

df <- read.csv("model.csv")


### Corelation Analysis ###
var_list <- c(
            'project_length_Hours', 'project_length_Days', 
            'project_length_Weeks', 
            "bounty_type_Bug", "bounty_type_Code_Review", "bounty_type_Design", "bounty_type_Documentation", "bounty_type_Feature",
            "bounty_type_Improvement","bounty_type_Other","bounty_type_Project","bounty_type_Security", "issue_timeout",
            "experience_level_Beginner",
            'experience_level_Advanced', 
            'experience_level_Intermediate',
            'repo_forks_count',
            "repo_language_JavaScript",
            "repo_language_TypeScript", 
            'repo_language_Others',
            'repo_stargazers_count', 
            'repo_watchers_count', 
            'repo_open_issues_count',
            'repo_subscribers_count', 
            'repo_size', 'code_additions', 'code_deletions',
            'code_changed_files', 'code_finish_time', 'issue_len_description',
            'fulfillments_len',
            'bounty_num',
            'bounty_change_num', 
            'owner_followers')

df_sub <- df[, var_list]
df_sub <- as.data.frame(lapply(df_sub, as.numeric))

# Spearman
correlation_matrix <- cor(df_sub, method = "spearman", use = "complete.obs")
capture.output(correlation_matrix, file = "model_cor&redun_anlysis.txt")

high_cor_vars <- which(abs(correlation_matrix) > 0.7, arr.ind = TRUE)
high_cor_vars <- high_cor_vars[high_cor_vars[,1] != high_cor_vars[,2], ]  

high_cor_groups <- list()
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

# choose one variable from each group
set.seed(100)  
remove_vars <- c()
for (group in high_cor_groups) {
  keep_var <- sample(group, 1)  
  remove_vars <- c(remove_vars, setdiff(group, keep_var))  
}

capture.output('spearman deleted variables:', file = "model_cor&redun_anlysis.txt", append=TRUE)
capture.output(remove_vars, file = "model_cor&redun_anlysis.txt", append=TRUE)
selected_vars <- setdiff(var_list, remove_vars)
capture.output('spearman reserved variables:', file = "model_cor&redun_anlysis.txt", append=TRUE)
capture.output(selected_vars, file = "model_cor&redun_anlysis.txt", append=TRUE)


corrplot(correlation_matrix, method = "circle", type = "upper",
         tl.col = "black", tl.cex = 0.7, diag = FALSE)

# variable clustering
vclust <- varclus(~., data = df_sub, similarity = "spearman", trans = "abs")
png("Hierarchical.png", width = 800, height = 600)
plot(vclust)
abline(h = 0.3, col = "red", lty = 2)  # (|ρ|=0.7)
dev.off()




### Redundancy Analysis ###
df_sub <- df[, selected_vars]
df_sub <- as.data.frame(lapply(df_sub, as.numeric))
dd <- datadist(df_sub)
options(datadist = "dd")

redun_result <- redun(~ ., 
                      data = df_sub,
                      nk = 0, 
                      r2 = 0.9)

capture.output('result of redundancy analysis:', file = "model_cor&redun_anlysis.txt", append=TRUE)
capture.output(redun_result, file = "model_cor&redun_anlysis.txt", append=TRUE)


final_vars <- setdiff(selected_vars, redun_result$Out)
capture.output('final variables:', file = "model_cor&redun_anlysis.txt", append=TRUE)
capture.output(final_vars, file = "model_cor&redun_anlysis.txt", append=TRUE)



### Model Building and Bootstrap Optimism R^2 ###

response_var <- "value_in_usdt"
gam_formula <- as.formula(paste(response_var, "~", paste(final_vars, collapse = " + ")))

# orginal model
original_model <- gam(gam_formula, data = df, method = "REML")


original_summary <- summary(original_model)
original_r2 <- original_summary$r.sq
n_obs <- nrow(df)


# Bootstrap parameters
n_boot <- 1000
optimism_values <- numeric(n_boot)

pb <- txtProgressBar(min = 0, max = n_boot, style = 3)
for (i in 1:n_boot) {
  tryCatch({
    boot_indices <- sample(n_obs, size = n_obs, replace = TRUE)
    boot_data <- df[boot_indices, ]
    
    # bootstrap model
    boot_model <- gam(gam_formula, data = boot_data, method = "REML")
    
    boot_summary <- summary(boot_model)
    boot_r2 <- boot_summary$r.sq
    
    # performance on original data
    pred_orig <- predict(boot_model, newdata = df)
    ss_total <- sum((df[[response_var]] - mean(df[[response_var]]))^2)
    ss_residual <- sum((df[[response_var]] - pred_orig)^2)
    r2_orig <- 1 - (ss_residual / ss_total)
    
    optimism_values[i] <- boot_r2 - r2_orig
    

    capture.output(
      cat("=== Bootstrap Iteration", i, "===\n"),
      print(boot_summary),
      cat("\nBootstrap R²:", boot_r2),
      cat("\nOriginal Data R²:", r2_orig),
      cat("\nOptimism:", optimism_values[i]),
      file = paste0("modelSummarys/model_", sprintf("%04d", i), ".txt"))
    }, error = function(e) {
      message("Error in iteration ", i, ": ", conditionMessage(e))
    })
  
  setTxtProgressBar(pb, i)
}

close(pb)


average_optimism <- mean(optimism_values, na.rm = TRUE)


optimism_r2 <- original_r2 - average_optimism


capture.output(
  cat("=== Final Model Summary ===\n"),
  print(summary(original_model)),
  cat("\n\n=== Bootstrap Validation Results ===\n"),
  cat("Original R²:", original_r2, "\n"),
  cat("Average Optimism:", average_optimism, "\n"),
  cat("Optimism R²:", optimism_r2, "\n"),
  cat("Number of Successful Bootstraps:", sum(!is.na(optimism_values)), "\n"),
  file = "model_summary.txt"
)

