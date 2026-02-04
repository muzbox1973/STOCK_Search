import CryptoJS from 'crypto-js';

const SECRET_SALT = 'stock-dashboard-v1-salt';

export const encryptKey = (key: string): string => {
    return CryptoJS.AES.encrypt(key, SECRET_SALT).toString();
};

export const decryptKey = (encryptedKey: string): string => {
    try {
        const bytes = CryptoJS.AES.decrypt(encryptedKey, SECRET_SALT);
        return bytes.toString(CryptoJS.enc.Utf8);
    } catch (e) {
        console.error('Decryption failed', e);
        return '';
    }
};
