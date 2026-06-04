/// Fast hash fingerprinter: djb2, CRC32. WASM memory at ptr.
fn djb2(data: &[u8]) -> u64 { let mut h:u64=5381; for &b in data { h=h.wrapping_mul(33).wrapping_add(b as u64); } h }
fn crc32(data: &[u8]) -> u32 { let mut c:u32=0xFFFFFFFF; for &b in data { c^=b as u32; for _ in 0..8 { if c&1!=0 { c=(c>>1)^0xEDB88320; } else { c>>=1; } } } !c }

fn write_result(ptr: *mut u8, s: &str) -> i32 {
    let b = s.as_bytes();
    unsafe { std::ptr::copy_nonoverlapping(b.as_ptr(), ptr, b.len()); }
    b.len() as i32
}

#[no_mangle]
pub extern "C" fn execute(ptr: *mut u8, len: usize) -> i32 {
    let input = unsafe { std::slice::from_raw_parts(ptr as *const u8, len) };
    let s = match std::str::from_utf8(input) { Ok(v) => v, Err(_) => return -1 };
    // Simple JSON parsing: {"text":"...","algorithm":"..."}
    let text = extract_str(s, "text").unwrap_or("");
    let algo = extract_str(s, "algorithm").unwrap_or("combined");
    let data = text.as_bytes();
    let hash = match algo {
        "crc32" => format!("{:08x}", crc32(data)),
        "djb2" => format!("{:016x}", djb2(data)),
        _ => format!("{:016x}_{:08x}", djb2(data), crc32(data)),
    };
    write_result(ptr, &format!("{{\"hash\":\"{}\",\"algo\":\"{}\",\"len\":{}}}", hash, algo, data.len()))
}

fn extract_str<'a>(json: &'a str, key: &str) -> Option<&'a str> {
    let mut pos = json.find(&format!("\"{}\"", key))?;
    pos = json[pos..].find(':')? + pos + 1;
    // skip whitespace
    while pos < json.len() && json.as_bytes()[pos] == b' ' { pos += 1; }
    if pos >= json.len() || json.as_bytes()[pos] != b'"' { return None; }
    pos += 1;
    let end = json[pos..].find('"')?;
    Some(&json[pos..pos+end])
}

fn extract_num(json: &str, key: &str) -> Option<u64> {
    let mut pos = json.find(&format!("\"{}\"", key))?;
    pos = json[pos..].find(':')? + pos + 1;
    while pos < json.len() && json.as_bytes()[pos] == b' ' { pos += 1; }
    let end = json[pos..].find(|c:char| !c.is_ascii_digit())?;
    json[pos..pos+end].parse().ok()
}

fn main() {}