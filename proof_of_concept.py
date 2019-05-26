#!python
# proof_of_concept.py - Data Visualization directly from mssql database
import typing
import os
import sqlalchemy
import urllib
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
import matplotlib.pyplot as plt


def create_engine() -> sqlalchemy.engine.base.Engine:
    """
    Creates the database engine needed to interact with the server.
    Ideally, this function would be different in one way:
    The network could use Active Domain/Windows Authentication. This would remove the need for UID and PWD
    parameters in the connection string, instead using Trusted_Connection=True.
    """
    DRIVER = r"{ODBC Driver 17 for SQL Server}"
    SERVER = os.getenv("MSSQL_SERVER")
    DATABASE = os.getenv("MSSQL_DB")
    UID = os.getenv("UID")
    PWD = os.getenv("PWD")
    connection_string = "DRIVER={0};Server={1};Database={2};UID={3};PWD={4}".format(DRIVER, SERVER, DATABASE, UID, PWD)
    # urllib solution from jmagnusson on SO https://stackoverflow.com/a/7399585
    quoted = urllib.parse.quote_plus(connection_string)
    engine = sqlalchemy.create_engine("mssql+pyodbc:///?odbc_connect={0}".format(quoted))
    return engine


def mock_process_df() -> pd.DataFrame:
    """
    Create some mock process data and put it in a pandas DataFrame,
    in order to add it to the database.
    In normal use, the data of interest are already in a SQL database.
    """
    mocked_length = 2000
    exp_param = np.array([100 + np.exp(x/200 - 1) for x in range(mocked_length)])
    const_param = np.ones(mocked_length) * 100
    rand_param = np.random.randint(98, 102, size=mocked_length)
    sin_param = np.sin(exp_param) + 100
    data = {
        "exp_param": exp_param,
        "const_param": const_param,
        "rand_param": rand_param,
        "sin_param": sin_param,
    }
    return pd.DataFrame(data=data, index=pd.date_range("2017", freq="D", periods=mocked_length))


def visualize_process(engine: sqlalchemy.engine.base.Engine) -> None:
    """
    Pull some data from the SQL Server database using SQL queries, and then use
    matplotlib to make plots.

    In this example, a subset of the data (2018) are queried from the database.
    Alternatively, the entire table could be selected and made into a DataFrame (SELECT * FROM Process).
    In this case, 2018 could be selected using a pandas selection.
    """
    query = "SELECT * FROM Process WHERE date >= '2018/01/01' AND date < '2019/01/01'"
    process_data = pd.read_sql(query, engine)

    # line plot of 3 parameters
    matplotlib.style.use("ggplot")
    ax1 = process_data.plot.line("date", "exp_param", label="Exponential Parameter")
    ax2 = process_data.plot.line("date", "const_param", ax=ax1, label="Constant Parameter")
    ax3 = process_data.plot.line("date", "sin_param", ax=ax1, label="Sinusoidal Parameter")
    plt.title("2018 Process Parameter Measurements")
    plt.legend()
    plt.savefig("visualizations/three_parameters.png", bbox_inches="tight")
    plt.close()

    # linear regression of exponential and sinusoidal parameters
    plt.style.use("ggplot")
    exponential = process_data["exp_param"]
    sinusoidal = process_data["sin_param"]
    slope, intercept, r_value, p_value, std_err = stats.linregress(exponential, sinusoidal)
    plt.plot(exponential, sinusoidal)
    plt.plot(exponential, slope * exponential + intercept, "--")
    plt.text(104, 100.5, "$r^2$ = {0:.6f}".format(r_value ** 2))
    plt.title("Sinusoidal vs. Exponential Parameters")
    plt.savefig("visualizations/sin_vs_exp.png", bbox_inches="tight")
    plt.close()

    # sin regression of exponential and sinusoidal parameters
    # this will work very well, because I mocked the data myself
    sin_exponential = np.sin(exponential) + 100
    slope, intercept, r_value, p_value, std_err = stats.linregress(sin_exponential, sinusoidal)
    plt.plot(sin_exponential, sinusoidal)
    plt.plot(sin_exponential, slope * sin_exponential + intercept, "--")
    plt.text(99, 100, "$r^2$ = {0:.6f}".format(r_value ** 2))
    plt.title(r"Sinusoidal vs. $\sin$(Exponential) Parameters")
    plt.savefig("visualizations/sin_vs_sinexp.png", bbox_inches="tight")
    plt.close()


def main():
    engine = create_engine()

    process_df = mock_process_df()
    process_df.to_sql("Process", engine, if_exists="replace", index_label="date")

    visualize_process(engine)


if __name__ == "__main__":
    main()
