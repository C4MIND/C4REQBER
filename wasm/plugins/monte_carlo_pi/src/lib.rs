/// Monte Carlo π — writes result to WASM memory at ptr.
use std::arch::wasm32;

static mut SEED: u64 = 12345u64;

fn rand_f64() -> f64 {
    unsafe {
        SEED = SEED.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        (SEED as f64) / (u64::MAX as f64)
    }
}

fn write_result(ptr: *mut u8, json_str: &str) -> i32 {
    let bytes = json_str.as_bytes();
    unsafe { std::ptr::copy_nonoverlapping(bytes.as_ptr(), ptr, bytes.len()); }
    bytes.len() as i32
}

#[no_mangle]
pub extern "C" fn execute(ptr: *mut u8, len: usize) -> i32 {
    let input = unsafe { std::slice::from_raw_parts(ptr as *const u8, len) };
    let json: serde_json::Value = match serde_json::from_slice(input) {
        Ok(v) => v,
        Err(e) => return write_result(ptr, &format!("{{\"error\":\"parse:{}\"}}", e)),
    };
    let n = json.get("iterations").and_then(|v| v.as_u64()).unwrap_or(1000).min(10_000_000);
    let mut inside = 0u64;
    for _ in 0..n {
        let x = rand_f64(); let y = rand_f64();
        if x*x + y*y <= 1.0 { inside += 1; }
    }
    let pi = 4.0 * inside as f64 / n as f64;
    let out = format!("{{\"pi\":{:.10},\"inside\":{},\"iterations\":{}}}", pi, inside, n);
    write_result(ptr, &out)
}

fn main() {}