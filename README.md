
# LogistiX

LogistiX is a decision support tool for facility location in logistics network design. It helps make decisions about the optimal placement of distribution centers in a logistics network based on user-defined parameters.


## Features

- Visualization of the logistics network on a map, displaying the locations of plants, customers, distribution centers, clustered distribution centers, and optimized distribution centers.

- A table showing the distribution center assignments for each customer and product.



## Usage

- Data Preparation :

    - Provide the data file containing locations informations.
    - Choose the number of plants, customers, distribution centers and number of products.
    - Fix seed for the random generator
    - Set optimization parameters (number of clusters and DCs to open)
    - Click the "Cluster and Optimize" button to perform optimization based on the defined parameters.

- Optimization Dashboard :
    - The map displays the locations of plants, customers, distribution centers, clustered distribution centers, and optimized distribution centers.
    - A table displays the distribution center assignments for each customer and product.


## Getting Started

Clone the repository:

```bash
  git clone https://github.com/medamineannouch/LogistiX.git
```
Install dependencies:

```bash
  pip install -r requirements.txt

```
Run the application:

```bash
  python app.py


```
    
## Acknowledgements

- [Gurobi Optimization Solver](https://www.gurobi.com/): Used for solving complex optimization problems.

- [Dash Framework](https://dash.plotly.com/): The Python web framework behind the interactive web application.

- [Agglomerative Clustering](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html): Employed for enhancing logistics network design.

- Other Dependencies:
  - [NumPy](https://numpy.org/): For numerical computations in Python.
  - [Pandas](https://pandas.pydata.org/): Data manipulation and analysis library.
  - [Plotly](https://plotly.com/): Interactive plotting and visualization library.


## Screenshots


![2](https://github.com/medamineannouch/LogistiX/assets/95173325/9ed22c1a-9e8f-4259-adb4-5cabbb6d9a19)



