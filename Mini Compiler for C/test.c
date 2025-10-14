// test5.c - Comprehensive arithmetic and control-flow test

int add(int x, int y) {
    return x + y;
}

int power(int base, int exp) {
    int result = 1;
    int i = 0;
    while (i < exp) {
        result = result * base;
        i = i + 1;
    }
    return result;
}

int main() {
    int a = add(2, 3);       // expect 5
    print(a);

    int b = power(a, 3);     // 5^3 = 125
    print(b);

    int sum = 0;
    int i = 1;
    while (i <= 5) {
        sum = sum + i;
        i = i + 1;
    }
    print(sum);              // 1 + 2 + 3 + 4 + 5 = 15

    if (b > 100) {
        print(999);
    } else if (b > 50) {
        print(555);
    } else {
        print(111);
    }
    print("hello");
    return sum;
}
