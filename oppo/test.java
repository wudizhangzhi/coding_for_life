import java.util.Arrays;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.io.UnsupportedEncodingException;


class Hello {
    public static String signMD5(String aValue, String aKey, String encoding) {
        byte[] keyb;
        byte[] value;
        // if (Utilities.isEmpty(encoding)) {
        //     encoding = DEFAULT_ENCODING;
        // }
        byte[] k_ipad = new byte[64];
        byte[] k_opad = new byte[64];
        try {
            keyb = aKey.getBytes(encoding);
            value = aValue.getBytes(encoding);
        } catch (UnsupportedEncodingException e) {
            keyb = aKey.getBytes();
            value = aValue.getBytes();
        }
        Arrays.fill(k_ipad, keyb.length, 64, (byte) 54);
        Arrays.fill(k_opad, keyb.length, 64, (byte) 92);
        for (int i = 0; i < keyb.length; i++) {
            k_ipad[i] = (byte) (keyb[i] ^ 54);
            k_opad[i] = (byte) (keyb[i] ^ 92);
        }
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            md.update(k_ipad);
            md.update(value);
            byte[] dg = md.digest();
            md.reset();
            md.update(k_opad);
            md.update(dg, 0, 16);
            return toHex(md.digest());
        } catch (NoSuchAlgorithmException e2) {
            return null;
        }
    }

    public static String toHex(byte[] input) {
        if (input == null) {
            return null;
        }
        StringBuilder output = new StringBuilder(input.length * 2);
        for (byte b : input) {
            int current = b & 0X000000ff;
            if (current < 16) {
                output.append("0");
            }
            output.append(Integer.toString(current, 16));
        }
        return output.toString();
    }

     public static void main (String args[]){
         // this.sign = formatSign(sign);
         // return HmacHelper.signMD5(this.appKey + this.loginName + this.passWord, sign);
         System.out.println(signMD5("usercenter170850249083ce25a66d5b3a8cd661024fea6c79388", "9effeac61b7ad92a9bef3da596f2158b", "UTF-8"));
     }
}
