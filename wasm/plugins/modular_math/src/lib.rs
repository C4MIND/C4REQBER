/// Modular math: powmod, gcd, isprime. WASM memory at ptr.
fn modpow(mut b: u64, mut e: u64, m: u64) -> u64 {
    if m==1{return 0;} let mut r:u64=1; b%=m;
    while e>0 { if e&1!=0 { r=((r as u128)*(b as u128)%(m as u128)) as u64; } e>>=1; b=((b as u128)*(b as u128)%(m as u128)) as u64; } r
}
fn gcd(mut a:u64,mut b:u64)->u64 { while b!=0 { let t=b; b=a%b; a=t; } a }
fn is_prime(n:u64)->bool {
    if n<2{return false;}if n==2||n==3{return true;}if n%2==0{return false}
    let mut d=n-1;let mut s=0;while d%2==0{d/=2;s+=1}
    for &a in &[2,3,5,7,11,13] { if a>=n{continue}
        let mut x=modpow(a,d,n);if x==1||x==n-1{continue}
        let mut ok=false; for _ in 0..s-1 { x=((x as u128)*(x as u128)%(n as u128)) as u64; if x==n-1{ok=true;break} }
        if !ok{return false} } true
}

fn extract_num(json: &str, key: &str) -> Option<u64> {
    let mut pos = json.find(&format!("\"{}\"", key))?;
    pos = json[pos..].find(':')? + pos + 1;
    while pos < json.len() && json.as_bytes()[pos] == b' ' { pos += 1; }
    let end = json[pos..].find(|c:char| !c.is_ascii_digit())?;
    json[pos..pos+end].parse().ok()
}
fn extract_str<'a>(json: &'a str, key: &str) -> Option<&'a str> {
    let mut pos = json.find(&format!("\"{}\"", key))?;
    pos = json[pos..].find(':')? + pos + 1;
    while pos < json.len() && json.as_bytes()[pos] == b' ' { pos += 1; }
    if pos >= json.len() || json.as_bytes()[pos] != b'"' { return None; }
    pos += 1;
    let end = json[pos..].find('"')?;
    Some(&json[pos..pos+end])
}

fn write_result(ptr: *mut u8, s: &str) -> i32 {
    let b = s.as_bytes();
    unsafe { std::ptr::copy_nonoverlapping(b.as_ptr(), ptr, b.len()); }
    b.len() as i32
}

#[no_mangle]
pub extern "C" fn execute(ptr: *mut u8, len: usize) -> i32 {
    let input = unsafe { std::slice::from_raw_parts(ptr as *const u8, len) };
    let s = match std::str::from_utf8(input) { Ok(v) => v, Err(_) => return -1 };
    let op = extract_str(s, "op").unwrap_or("gcd");
    let a = extract_num(s, "a").unwrap_or(0);
    let b = extract_num(s, "b").unwrap_or(0);
    let m = extract_num(s, "m").unwrap_or(1);
    let result = match op {
        "modpow" => modpow(a, b, m.max(1)),
        "gcd" => gcd(a, b),
        "isprime" => if is_prime(a) { 1 } else { 0 },
        _ => 0,
    };
    write_result(ptr, &format!("{{\"op\":\"{}\",\"result\":{}}}", op, result))
}

fn main() {}