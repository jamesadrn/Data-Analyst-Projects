import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

class EDA_Pipeline:
    """
    Automated EDA Pipeline for Data Analysis with Datetime Support
    """
    
    def __init__(self, df, target_col=None, categorical_threshold=10, high_cardinality_threshold=100):
        """
        Initialize EDA Analyzer
        
        Parameters:
        -----------
        df : pandas DataFrame
        target_col : str, target column name for bivariate analysis
        categorical_threshold : int, max unique values to treat as categorical
        high_cardinality_threshold : int, threshold for high cardinality (default 100)
        """
        self.df = df.copy()
        self.target_col = target_col
        self.categorical_threshold = categorical_threshold
        self.high_cardinality_threshold = high_cardinality_threshold
        
        # Auto-detect datetime columns
        self.datetime_cols = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                self.datetime_cols.append(col)
            elif df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col]):
                # Try to parse as datetime
                try:
                    pd.to_datetime(df[col], errors='raise')
                    self.df[col] = pd.to_datetime(df[col])
                    self.datetime_cols.append(col)
                except:
                    pass
        
        # Auto-detect numerical columns (exclude datetime)
        self.numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        # Remove target from numerical if it exists
        if target_col in self.numerical_cols:
            self.numerical_cols.remove(target_col)
        
        # Remove datetime columns from numerical
        self.numerical_cols = [col for col in self.numerical_cols if col not in self.datetime_cols]
        
        # Detect categorical - NOW WITH STRING SUPPORT
        self.categorical_cols = []
        self.high_cardinality_cols = []
        
        for col in df.columns:
            if col == target_col or col in self.datetime_cols:
                continue
            
            n_unique = df[col].nunique()
            
            # Check if it's categorical type OR object/string type OR low-cardinality numerical
            is_categorical_dtype = pd.api.types.is_categorical_dtype(df[col])
            is_object_or_string = df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col])
            is_low_cardinality_numeric = (df[col].dtype in ['int64', 'float64'] and n_unique <= categorical_threshold)
            
            # If it's categorical, object, or string type
            if is_categorical_dtype or is_object_or_string or is_low_cardinality_numeric:
                # Split based on cardinality
                if n_unique <= high_cardinality_threshold:
                    # Low cardinality -> categorical
                    self.categorical_cols.append(col)
                    print(f"✓ '{col}' added to categorical (unique values: {n_unique})")
                else:
                    # High cardinality -> show top 5 only
                    self.high_cardinality_cols.append(col)
                    print(f"⚠️  '{col}' is high cardinality (unique values: {n_unique}) - will show top 5 only")
        
        print(f"\n{'='*60}")
        print(f"✓ Detected {len(self.numerical_cols)} numerical columns")
        print(f"✓ Detected {len(self.categorical_cols)} categorical columns (≤{high_cardinality_threshold} unique)")
        print(f"✓ Detected {len(self.datetime_cols)} datetime columns")
        print(f"✓ Detected {len(self.high_cardinality_cols)} high-cardinality columns (>{high_cardinality_threshold} unique)")
        if target_col:
            print(f"✓ Target column: {target_col}")
        print(f"{'='*60}")
        
        # Show detailed breakdown
        print("\n--- Column Type Breakdown ---")
        if self.categorical_cols:
            print(f"Categorical: {self.categorical_cols}")
        if self.numerical_cols:
            print(f"Numerical: {self.numerical_cols}")
        if self.datetime_cols:
            print(f"Datetime: {self.datetime_cols}")
        if self.high_cardinality_cols:
            print(f"High Cardinality: {self.high_cardinality_cols}")
    
    def data_overview(self):
        """Generate data overview report"""
        print("\n" + "="*60)
        print("DATA OVERVIEW")
        print("="*60)
        
        print(f"\nDataset Shape: {self.df.shape[0]:,} rows × {self.df.shape[1]} columns")
        print(f"Memory Usage: {self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        print("\n--- Data Types ---")
        print(self.df.dtypes.value_counts())
        
        print("\n--- Missing Values ---")
        missing = self.df.isnull().sum()
        if missing.sum() > 0:
            missing_pct = (missing / len(self.df) * 100).round(2)
            missing_df = pd.DataFrame({
                'Missing': missing[missing > 0],
                'Percentage': missing_pct[missing > 0]
            }).sort_values('Missing', ascending=False)
            print(missing_df)
        else:
            print("No missing values found!")
        
        print(f"\n--- Duplicates ---")
        duplicates = self.df.duplicated().sum()
        print(f"Total duplicates: {duplicates} ({duplicates/len(self.df)*100:.2f}%)")
        
        return self
    
    def univariate_datetime(self, save_plots=False):
        """Analyze datetime variables"""
        if not self.datetime_cols:
            return self
            
        print("\n" + "="*60)
        print("UNIVARIATE ANALYSIS - DATETIME FEATURES")
        print("="*60)
        
        for col in self.datetime_cols:
            print(f"\n--- {col.upper()} ---")
            
            # Basic statistics
            print(f"Earliest date: {self.df[col].min()}")
            print(f"Latest date: {self.df[col].max()}")
            print(f"Date range: {(self.df[col].max() - self.df[col].min()).days} days")
            print(f"Missing values: {self.df[col].isnull().sum()} ({self.df[col].isnull().sum()/len(self.df)*100:.2f}%)")
            
            # Extract temporal features
            df_temp = self.df[col].dropna()
            
            # Time-based distributions
            fig, axes = plt.subplots(2, 3, figsize=(18, 10))
            fig.suptitle(f'Temporal Analysis of {col}', fontsize=16, y=1.00)
            
            # Year distribution
            if df_temp.dt.year.nunique() > 1:
                df_temp.dt.year.value_counts().sort_index().plot(kind='bar', ax=axes[0, 0], edgecolor='black', alpha=0.7)
                axes[0, 0].set_title('Distribution by Year')
                axes[0, 0].set_xlabel('Year')
                axes[0, 0].set_ylabel('Count')
                axes[0, 0].tick_params(axis='x', rotation=45)
            else:
                axes[0, 0].text(0.5, 0.5, 'Single Year Data', ha='center', va='center')
                axes[0, 0].set_title('Distribution by Year')
            
            # Month distribution
            month_counts = df_temp.dt.month.value_counts().sort_index()
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            axes[0, 1].bar(range(1, 13), [month_counts.get(i, 0) for i in range(1, 13)], edgecolor='black', alpha=0.7)
            axes[0, 1].set_xticks(range(1, 13))
            axes[0, 1].set_xticklabels(month_names, rotation=45)
            axes[0, 1].set_title('Distribution by Month')
            axes[0, 1].set_xlabel('Month')
            axes[0, 1].set_ylabel('Count')
            
            # Day of week distribution
            dow_counts = df_temp.dt.dayofweek.value_counts().sort_index()
            dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            axes[0, 2].bar(range(7), [dow_counts.get(i, 0) for i in range(7)], edgecolor='black', alpha=0.7)
            axes[0, 2].set_xticks(range(7))
            axes[0, 2].set_xticklabels(dow_names, rotation=45)
            axes[0, 2].set_title('Distribution by Day of Week')
            axes[0, 2].set_xlabel('Day')
            axes[0, 2].set_ylabel('Count')
            
            # Hour distribution (if time component exists)
            if (df_temp.dt.hour != 0).any():
                df_temp.dt.hour.value_counts().sort_index().plot(kind='bar', ax=axes[1, 0], edgecolor='black', alpha=0.7)
                axes[1, 0].set_title('Distribution by Hour')
                axes[1, 0].set_xlabel('Hour')
                axes[1, 0].set_ylabel('Count')
            else:
                axes[1, 0].text(0.5, 0.5, 'No Time Component', ha='center', va='center')
                axes[1, 0].set_title('Distribution by Hour')
            
            # Quarter distribution
            quarter_counts = df_temp.dt.quarter.value_counts().sort_index()
            axes[1, 1].bar(range(1, 5), [quarter_counts.get(i, 0) for i in range(1, 5)], edgecolor='black', alpha=0.7)
            axes[1, 1].set_xticks(range(1, 5))
            axes[1, 1].set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'])
            axes[1, 1].set_title('Distribution by Quarter')
            axes[1, 1].set_xlabel('Quarter')
            axes[1, 1].set_ylabel('Count')
            
            # Timeline plot
            date_counts = df_temp.value_counts().sort_index()
            axes[1, 2].plot(date_counts.index, date_counts.values, marker='o', linestyle='-', markersize=2, linewidth=1)
            axes[1, 2].set_title('Timeline of Records')
            axes[1, 2].set_xlabel('Date')
            axes[1, 2].set_ylabel('Count')
            axes[1, 2].tick_params(axis='x', rotation=45)
            axes[1, 2].grid(True, alpha=0.3)
            
            plt.tight_layout()
            if save_plots:
                plt.savefig(f'univariate_datetime_{col}.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            # Summary statistics for temporal components
            print("\n--- Temporal Component Statistics ---")
            print(f"Most common year: {df_temp.dt.year.mode()[0] if len(df_temp.dt.year.mode()) > 0 else 'N/A'}")
            print(f"Most common month: {df_temp.dt.month.mode()[0] if len(df_temp.dt.month.mode()) > 0 else 'N/A'}")
            print(f"Most common day of week: {dow_names[df_temp.dt.dayofweek.mode()[0]] if len(df_temp.dt.dayofweek.mode()) > 0 else 'N/A'}")
            if (df_temp.dt.hour != 0).any():
                print(f"Most common hour: {df_temp.dt.hour.mode()[0] if len(df_temp.dt.hour.mode()) > 0 else 'N/A'}:00")
        
        return self
    
    def univariate_numerical(self, save_plots=False):
        """Analyze numerical variables"""
        if not self.numerical_cols:
            return self
            
        print("\n" + "="*60)
        print("UNIVARIATE ANALYSIS - NUMERICAL FEATURES")
        print("="*60)
        
        for col in self.numerical_cols:
            print(f"\n--- {col.upper()} ---")
            print(self.df[col].describe())
            print(f"Skewness: {self.df[col].skew():.3f}")
            print(f"Kurtosis: {self.df[col].kurtosis():.3f}")
            
            # Detect outliers
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = self.df[(self.df[col] < Q1 - 1.5*IQR) | (self.df[col] > Q3 + 1.5*IQR)]
            print(f"Outliers: {len(outliers)} ({len(outliers)/len(self.df)*100:.2f}%)")
            
            # Visualization
            fig, axes = plt.subplots(1, 3, figsize=(15, 4))
            
            # Histogram
            axes[0].hist(self.df[col].dropna(), bins=30, edgecolor='black', alpha=0.7)
            axes[0].set_title(f'Distribution of {col}')
            axes[0].set_xlabel(col)
            axes[0].set_ylabel('Frequency')
            
            # Boxplot
            axes[1].boxplot(self.df[col].dropna())
            axes[1].set_title(f'Boxplot of {col}')
            axes[1].set_ylabel(col)
            
            # Q-Q plot
            from scipy import stats
            stats.probplot(self.df[col].dropna(), dist="norm", plot=axes[2])
            axes[2].set_title(f'Q-Q Plot of {col}')
            
            plt.tight_layout()
            if save_plots:
                plt.savefig(f'univariate_{col}.png', dpi=300, bbox_inches='tight')
            plt.show()
        
        return self
    
    def univariate_categorical(self, top_n=10, save_plots=False):
        """Analyze categorical variables (low cardinality)"""
        if not self.categorical_cols and not self.high_cardinality_cols:
            return self
            
        print("\n" + "="*60)
        print("UNIVARIATE ANALYSIS - CATEGORICAL FEATURES (LOW CARDINALITY)")
        print("="*60)
        
        for col in self.categorical_cols:
            print(f"\n--- {col.upper()} ---")
            print(f"Data type: {self.df[col].dtype}")
            n_unique = self.df[col].nunique()
            print(f"Unique values: {n_unique}")
            
            # Show all values for low cardinality
            print(f"\nValue counts (all {n_unique} categories):")
            print(self.df[col].value_counts())
            
            # Calculate percentages
            value_pct = (self.df[col].value_counts() / len(self.df) * 100).round(2)
            print(f"\nPercentage distribution:")
            print(value_pct)
            
            # Visualization - show all categories
            plt.figure(figsize=(14, 6))
            value_counts = self.df[col].value_counts()
            value_counts.plot(kind='bar', edgecolor='black', alpha=0.7, color='steelblue')
            plt.title(f'Distribution of {col} ({n_unique} categories)')
            plt.xlabel(col)
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right')
            
            # Add percentage on top of bars
            for i, v in enumerate(value_counts.values):
                plt.text(i, v + max(value_counts)*0.01, f'{value_pct.iloc[i]:.1f}%', 
                        ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            if save_plots:
                plt.savefig(f'univariate_{col}.png', dpi=300, bbox_inches='tight')
            plt.show()
        
        # Handle high cardinality columns - ALWAYS SHOW TOP 5
        if self.high_cardinality_cols:
            print("\n" + "="*60)
            print("UNIVARIATE ANALYSIS - HIGH CARDINALITY COLUMNS (TOP 5 ONLY)")
            print("="*60)
            
            for col in self.high_cardinality_cols:
                print(f"\n--- {col.upper()} ---")
                print(f"Data type: {self.df[col].dtype}")
                n_unique = self.df[col].nunique()
                print(f"Unique values: {n_unique:,}")
                print(f"Total records: {len(self.df):,}")
                print(f"Cardinality ratio: {n_unique/len(self.df)*100:.2f}%")
                
                # Always show top 5
                top_5 = self.df[col].value_counts().head(5)
                top_5_pct = (top_5 / len(self.df) * 100).round(2)
                
                print(f"\n📊 Top 5 most frequent values:")
                for idx, (value, count) in enumerate(top_5.items(), 1):
                    print(f"  {idx}. {value}: {count:,} ({top_5_pct.iloc[idx-1]:.2f}%)")
                
                # Visualization - Top 5 only
                plt.figure(figsize=(14, 6))
                top_5.plot(kind='bar', edgecolor='black', alpha=0.7, color='coral')
                plt.title(f'Top 5 Values of {col} (out of {n_unique:,} unique values)')
                plt.xlabel(col)
                plt.ylabel('Count')
                plt.xticks(rotation=45, ha='right')
                
                # Add percentage on bars
                for i, v in enumerate(top_5.values):
                    plt.text(i, v + max(top_5)*0.01, f'{top_5_pct.iloc[i]:.1f}%', 
                            ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                if save_plots:
                    plt.savefig(f'univariate_{col}_top5.png', dpi=300, bbox_inches='tight')
                plt.show()
        
        return self
    
    def bivariate_datetime_analysis(self, save_plots=False):
        """Analyze relationship between datetime and target variable"""
        if self.target_col is None or not self.datetime_cols:
            return self
        
        print("\n" + "="*60)
        print(f"BIVARIATE ANALYSIS - DATETIME VS {self.target_col.upper()}")
        print("="*60)
        
        for col in self.datetime_cols:
            print(f"\n--- {col.upper()} VS {self.target_col.upper()} ---")
            
            df_temp = self.df[[col, self.target_col]].dropna()
            
            fig, axes = plt.subplots(2, 2, figsize=(16, 10))
            fig.suptitle(f'{col} vs {self.target_col}', fontsize=16, y=1.00)
            
            # Time series plot
            daily_stats = df_temp.groupby(df_temp[col].dt.date)[self.target_col].mean()
            axes[0, 0].plot(daily_stats.index, daily_stats.values, marker='o', markersize=2, linewidth=1)
            axes[0, 0].set_title(f'Average {self.target_col} Over Time')
            axes[0, 0].set_xlabel('Date')
            axes[0, 0].set_ylabel(f'Average {self.target_col}')
            axes[0, 0].tick_params(axis='x', rotation=45)
            axes[0, 0].grid(True, alpha=0.3)
            
            # By month
            monthly_stats = df_temp.groupby(df_temp[col].dt.month)[self.target_col].mean()
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            axes[0, 1].bar(monthly_stats.index, monthly_stats.values, edgecolor='black', alpha=0.7)
            axes[0, 1].set_xticks(range(1, 13))
            axes[0, 1].set_xticklabels(month_names, rotation=45)
            axes[0, 1].set_title(f'Average {self.target_col} by Month')
            axes[0, 1].set_xlabel('Month')
            axes[0, 1].set_ylabel(f'Average {self.target_col}')
            
            # By day of week
            dow_stats = df_temp.groupby(df_temp[col].dt.dayofweek)[self.target_col].mean()
            dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            axes[1, 0].bar(dow_stats.index, dow_stats.values, edgecolor='black', alpha=0.7)
            axes[1, 0].set_xticks(range(7))
            axes[1, 0].set_xticklabels(dow_names, rotation=45)
            axes[1, 0].set_title(f'Average {self.target_col} by Day of Week')
            axes[1, 0].set_xlabel('Day of Week')
            axes[1, 0].set_ylabel(f'Average {self.target_col}')
            
            # By hour (if applicable)
            if (df_temp[col].dt.hour != 0).any():
                hourly_stats = df_temp.groupby(df_temp[col].dt.hour)[self.target_col].mean()
                axes[1, 1].bar(hourly_stats.index, hourly_stats.values, edgecolor='black', alpha=0.7)
                axes[1, 1].set_title(f'Average {self.target_col} by Hour')
                axes[1, 1].set_xlabel('Hour')
                axes[1, 1].set_ylabel(f'Average {self.target_col}')
            else:
                axes[1, 1].text(0.5, 0.5, 'No Time Component', ha='center', va='center')
                axes[1, 1].set_title(f'Average {self.target_col} by Hour')
            
            plt.tight_layout()
            if save_plots:
                plt.savefig(f'bivariate_datetime_{col}_vs_{self.target_col}.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            # Statistical summary
            print("\n--- Temporal Statistics ---")
            print(f"Overall average {self.target_col}: {df_temp[self.target_col].mean():.2f}")
            print(f"\nAverage by month:")
            print(monthly_stats.round(2))
            print(f"\nAverage by day of week:")
            for i, dow in enumerate(dow_names):
                if i in dow_stats.index:
                    print(f"{dow}: {dow_stats[i]:.2f}")
        
        return self
    
    def bivariate_analysis(self, save_plots=False):
        """Analyze relationship with target variable"""
        if self.target_col is None:
            print("\n⚠ No target column specified. Skipping bivariate analysis.")
            return self
        
        print("\n" + "="*60)
        print(f"BIVARIATE ANALYSIS - FEATURES VS {self.target_col.upper()}")
        print("="*60)
        
        # Numerical vs Target
        if self.numerical_cols:
            print("\n--- NUMERICAL FEATURES VS TARGET ---")
            for col in self.numerical_cols:
                correlation = self.df[[col, self.target_col]].corr().iloc[0, 1]
                print(f"\n{col} → Correlation: {correlation:.3f}")
                
                plt.figure(figsize=(10, 6))
                plt.scatter(self.df[col], self.df[self.target_col], alpha=0.5, edgecolors='k', linewidths=0.5)
                plt.xlabel(col)
                plt.ylabel(self.target_col)
                plt.title(f'{col} vs {self.target_col} (r={correlation:.3f})')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                if save_plots:
                    plt.savefig(f'bivariate_{col}_vs_{self.target_col}.png', dpi=300, bbox_inches='tight')
                plt.show()
        
        # Categorical vs Target
        if self.categorical_cols:
            print("\n--- CATEGORICAL FEATURES VS TARGET ---")
            for col in self.categorical_cols:
                stats = self.df.groupby(col)[self.target_col].agg(['mean', 'median', 'count', 'std'])
                print(f"\n{col}:")
                print(stats.sort_values('mean', ascending=False))
                
                fig, axes = plt.subplots(1, 2, figsize=(16, 6))
                
                # Bar plot
                stats['mean'].sort_values(ascending=False).plot(kind='bar', ax=axes[0], edgecolor='black', alpha=0.7)
                axes[0].set_title(f'Average {self.target_col} by {col}')
                axes[0].set_ylabel(f'Average {self.target_col}')
                axes[0].tick_params(axis='x', rotation=45)
                
                # Box plot
                self.df.boxplot(column=self.target_col, by=col, ax=axes[1])
                axes[1].set_title(f'{self.target_col} Distribution by {col}')
                axes[1].set_xlabel(col)
                plt.suptitle('')
                
                plt.tight_layout()
                if save_plots:
                    plt.savefig(f'bivariate_{col}_vs_{self.target_col}.png', dpi=300, bbox_inches='tight')
                plt.show()
        
        return self
    
    def correlation_matrix(self, save_plot=False):
        """Generate correlation matrix for numerical features"""
        if len(self.numerical_cols) < 2:
            print("\n⚠ Not enough numerical columns for correlation matrix")
            return self
        
        print("\n" + "="*60)
        print("CORRELATION MATRIX")
        print("="*60)
        
        # Include target if numerical
        cols_for_corr = self.numerical_cols.copy()
        if self.target_col and self.df[self.target_col].dtype in ['int64', 'float64']:
            cols_for_corr.append(self.target_col)
        
        corr_matrix = self.df[cols_for_corr].corr()
        
        # Print top correlations with target
        if self.target_col in cols_for_corr:
            print(f"\nTop correlations with {self.target_col}:")
            target_corr = corr_matrix[self.target_col].drop(self.target_col).sort_values(ascending=False)
            print(target_corr)
        
        # Visualization
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                   center=0, square=True, linewidths=1, cbar_kws={'label': 'Correlation'})
        plt.title('Correlation Matrix')
        plt.tight_layout()
        
        if save_plot:
            plt.savefig('correlation_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return self
    
    def multivariate_analysis(self, max_combinations=5, save_plots=False):
        """Analyze interactions between features"""
        if self.target_col is None or len(self.categorical_cols) < 2:
            print("\n⚠ Need target column and at least 2 categorical features for multivariate analysis")
            return self
        
        print("\n" + "="*60)
        print("MULTIVARIATE ANALYSIS - INTERACTION EFFECTS")
        print("="*60)
        
        # Analyze top combinations
        cat_cols_sample = self.categorical_cols[:max_combinations]
        
        for i, col1 in enumerate(cat_cols_sample):
            for col2 in cat_cols_sample[i+1:]:
                print(f"\n--- {col1.upper()} × {col2.upper()} ---")
                
                pivot = self.df.groupby([col1, col2])[self.target_col].mean().unstack()
                print(pivot)
                
                # Heatmap
                plt.figure(figsize=(12, 8))
                sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', 
                           cbar_kws={'label': f'Avg {self.target_col}'})
                plt.title(f'{col1} × {col2} Interaction Effect on {self.target_col}')
                plt.xlabel(col2)
                plt.ylabel(col1)
                plt.tight_layout()
                
                if save_plots:
                    plt.savefig(f'multivariate_{col1}_x_{col2}.png', dpi=300, bbox_inches='tight')
                plt.show()
        
        return self
    
    def generate_report(self, save_plots=False):
        """Run complete EDA pipeline"""
        print("\n" + "="*70)
        print(" "*5 + "AUTOMATED EDA REPORT")
        print("="*70)
        
        self.data_overview()
        self.univariate_datetime(save_plots=save_plots)
        self.univariate_numerical(save_plots=save_plots)
        self.univariate_categorical(save_plots=save_plots)
        self.correlation_matrix(save_plot=save_plots)
        
        if self.target_col:
            self.bivariate_datetime_analysis(save_plots=save_plots)
            self.bivariate_analysis(save_plots=save_plots)
            self.multivariate_analysis(save_plots=save_plots)
        
        print("\n" + "="*70)
        print("✓ EDA REPORT COMPLETED")
        print("="*70)
        
        return self


# ============= EXAMPLE USAGE =============
if __name__ == "__main__":
    # Test with different data types including string dtype
    print("Creating sample data with multiple dtypes (string, category, object)...\n")
    
    df_test = pd.DataFrame({
        'numeric_col': np.random.randn(1000),
        'low_card_string': pd.array(['A', 'B', 'C'] * 333 + ['A'], dtype='string'),  # String dtype, low cardinality
        'high_card_string': pd.array([f'ID_{i}' for i in range(1000)], dtype='string'),  # String dtype, high cardinality
        'category_col': pd.Categorical(['X', 'Y', 'Z'] * 333 + ['X']),  # Category dtype
        'object_col': ['P', 'Q'] * 500,  # Object dtype
        'date_col': pd.date_range('2024-01-01', periods=1000),
        'target': np.random.randn(1000)
    })
    
    print(f"DataFrame dtypes:")
    print(df_test.dtypes)
    print("\n" + "="*60 + "\n")
    
    # Initialize EDA Pipeline
    eda = EDA_Pipeline(df_test, target_col='target', high_cardinality_threshold=50)
    
    # Run analysis
    print("\n\n--- Running Univariate Categorical Analysis ---")
    eda.univariate_categorical()
    
    print("\n✅ Test completed! The script now handles:")
    print("   - String dtype (both low and high cardinality)")
    print("   - Category dtype") 
    print("   - Object dtype")
    print("   - Splits based on cardinality threshold")
    print("   - Shows TOP 5 for high cardinality columns")