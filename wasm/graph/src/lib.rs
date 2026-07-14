use wasm_bindgen::prelude::*;

/// Simple force-directed layout step (Fruchterman-Reingold).
///
/// # Arguments
/// * `nodes_x` - X positions
/// * `nodes_y` - Y positions  
/// * `edges_src` - Edge source indices
/// * `edges_tgt` - Edge target indices
/// * `width` - Canvas width
/// * `height` - Canvas height
/// * `k` - Optimal distance
///
/// # Returns
/// [new_x..., new_y...] flattened
#[wasm_bindgen]
pub fn force_directed_step(
    nodes_x: Vec<f64>,
    nodes_y: Vec<f64>,
    edges_src: Vec<usize>,
    edges_tgt: Vec<usize>,
    width: f64,
    height: f64,
    k: f64,
) -> Vec<f64> {
    let n = nodes_x.len();
    let mut new_x = nodes_x.clone();
    let mut new_y = nodes_y.clone();
    let mut vx = vec![0.0; n];
    let mut vy = vec![0.0; n];

    // Repulsion
    for i in 0..n {
        for j in (i + 1)..n {
            let dx = nodes_x[i] - nodes_x[j];
            let dy = nodes_y[i] - nodes_y[j];
            let dist_sq = dx * dx + dy * dy;
            let dist = dist_sq.sqrt().max(0.01);
            let force = (k * k) / dist;
            let fx = (dx / dist) * force;
            let fy = (dy / dist) * force;
            vx[i] += fx;
            vy[i] += fy;
            vx[j] -= fx;
            vy[j] -= fy;
        }
    }

    // Attraction
    for e in 0..edges_src.len() {
        let i = edges_src[e];
        let j = edges_tgt[e];
        let dx = nodes_x[j] - nodes_x[i];
        let dy = nodes_y[j] - nodes_y[i];
        let dist = (dx * dx + dy * dy).sqrt().max(0.01);
        let force = (dist * dist) / k;
        let fx = (dx / dist) * force;
        let fy = (dy / dist) * force;
        vx[i] += fx;
        vy[i] += fy;
        vx[j] -= fx;
        vy[j] -= fy;
    }

    // Apply velocity
    for i in 0..n {
        new_x[i] = (new_x[i] + vx[i]).clamp(10.0, width - 10.0);
        new_y[i] = (new_y[i] + vy[i]).clamp(10.0, height - 10.0);
    }

    new_x.extend(new_y);
    new_x
}
