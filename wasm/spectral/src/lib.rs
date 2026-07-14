use ndarray::{Array1, Array2, Axis};
use wasm_bindgen::prelude::*;

/// Compute spectral embedding of a graph Laplacian.
///
/// # Arguments
/// * `adjacency_flat` - Flattened adjacency matrix (n x n)
/// * `n` - Number of nodes
/// * `dimensions` - Embedding dimensions
///
/// # Returns
/// Flattened embedding matrix (n x dimensions)
#[wasm_bindgen]
pub fn spectral_embedding(adjacency_flat: Vec<f64>, n: usize, dimensions: usize) -> Vec<f64> {
    // Reshape adjacency
    let adj =
        Array2::from_shape_vec((n, n), adjacency_flat).unwrap_or_else(|_| Array2::zeros((n, n)));

    // Compute degree matrix
    let degrees: Array1<f64> = adj.sum_axis(Axis(1));

    // Compute symmetric normalized Laplacian: I - D^{-1/2} A D^{-1/2}
    let mut laplacian = Array2::zeros((n, n));
    for i in 0..n {
        for j in 0..n {
            if i == j {
                laplacian[[i, j]] = 1.0;
            }
            let di = degrees[i].sqrt().max(1e-10);
            let dj = degrees[j].sqrt().max(1e-10);
            laplacian[[i, j]] -= adj[[i, j]] / (di * dj);
        }
    }

    // Power iteration for top k eigenvectors (simplified)
    let mut embedding = Array2::zeros((n, dimensions));
    for d in 0..dimensions {
        let mut vec = Array1::from_iter((0..n).map(|i| (i as f64 + 1.0).sin()));
        vec = vec / vec.iter().map(|x| x * x).sum::<f64>().sqrt().max(1e-10);

        for _ in 0..50 {
            let mut new_vec = Array1::zeros(n);
            for i in 0..n {
                for j in 0..n {
                    new_vec[i] += laplacian[[i, j]] * vec[j];
                }
            }
            let norm = new_vec.iter().map(|x| x * x).sum::<f64>().sqrt().max(1e-10);
            vec = new_vec / norm;
        }

        for i in 0..n {
            embedding[[i, d]] = vec[i];
        }

        // Deflate
        for i in 0..n {
            for j in 0..n {
                laplacian[[i, j]] -= 2.0 * vec[i] * vec[j];
            }
        }
    }

    embedding.into_raw_vec()
}

/// Compute graph Laplacian from adjacency matrix.
#[wasm_bindgen]
pub fn graph_laplacian(adjacency_flat: Vec<f64>, n: usize) -> Vec<f64> {
    let adj =
        Array2::from_shape_vec((n, n), adjacency_flat).unwrap_or_else(|_| Array2::zeros((n, n)));
    let degrees = adj.sum_axis(Axis(1));
    let mut laplacian = Array2::zeros((n, n));

    for i in 0..n {
        laplacian[[i, i]] = degrees[i];
        for j in 0..n {
            laplacian[[i, j]] -= adj[[i, j]];
        }
    }

    laplacian.into_raw_vec()
}
