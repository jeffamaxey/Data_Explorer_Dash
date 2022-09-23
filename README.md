# Data_Explorer_Dash
## Data Exploration Tool Utilizing Plotly/Dash and Pandas

This is a basic tool that can read data files from disk, display them in a table format, and allow for the user to perform basic data exploration.


## Running the Application
### There are two provided options for running the application.

#### 1. Running Via Python
##### Download [Python3.1](https://www.python.org/downloads/release/python-3100/, "Python 3.1 Download Link") and Create A Virtual Environment For Running the Application.
```
virtualenv data_viewer_env
```

##### Activate Your New Virtual Environment.
```
Mac/Linux:
source venv/bin/activate

Windows:
data_viewer_env\Scripts\activate
```

##### Install the required Python packages from requirements.txt into your new virtual environment.
```
pip install -r requirements.txt
```

##### Run The Application
```
python app.py
```

#### 2. Running Via Executable (Windows Only)
##### Simply run the provided executable file to launch the application.

&nbsp;
## Using the Application


### Open Browser Window
##### The application will attempt to automatically open a browser window, and navigate to the proper page.
##### If this does not happen automatically, open a new browswer window and navigate to [localhost:8050](http://localhost:8050, "Page Where Application Is Served").

### Select Data Folder
##### First, choose a folder where your data resides with the (Data Path) input field.
##### Once a folder is specified, any potential data files within the folder will be set
##### as options in the (Select Dataset) dropdown.



### Select Dataset File
##### Selecting a dataset will load in the file to the data table.


### Data Filtering
##### From here, you can filter your data using the filter line at the top of the table.
##### The filtering queries accept a series of commands, like (=, >, <=, >=, etc.)
##### A full explanation of possible commands resides at which can be found [here](https://dash.plotly.com/datatable/filtering/, "Plotly Dash Filtering Documentation").


### Aggregations
##### You may also perform aggregations using the Group By and Aggregation Method dropdowns on the left.
##### These will allow you to group the data by category, and then perform aggregations on that group.


Ex: If you want to find the mean price of items for each item category, you would select: 
  >(Group By) -> Category
  >
  >(Aggregation Method) -> Mean


### Bar Plots
##### Aggregating the data will also display bar plots at the bottom of the table showing the results of the aggregation.
##### These bar plots respond to filtering and sorting of the table as you would expect.



### Page Size
##### The Page Size input field denotes the max number of rows for the table to display at any one time.



### Max Bar Plots Number
##### The Max Number Plot Bars slider denotes the maximum number of bars to plot.
That is, if:
> (Max Number Bar Plots) -> 20

then only the first 20 rows of the table will be rendered as bars in the bar plot.

### Download Filtered Data
#### The Download Filtered Data button will download as a .csv file, all the data currently contained in the data table.

&nbsp
## Notes of Interest


### Multi Group-By
##### Multiple Groups can be denoted in the Group By field. 
For instance:
>(Group By) -> [Category, Device Type Group]
>
>(Aggregation Method) -> Count

will give the count of how many products match each possible combination
of Category and Device Type categories.



### Filtering and Aggregating
##### If using filtering and aggregation at the same time, use aggregation first.
For instance, if you want to display the mean price of only the Luggage
category, you would do:

First,
>(Group By) -> Category
>
>(Aggregation Method) -> Mean

Then,
>(Category Filter Field) -> Luggage

### Accepted File Types
##### The accepted file types for this application are:
* ##### .csv
* ##### .xls
* ##### .xlsx
* ##### .xlsm
