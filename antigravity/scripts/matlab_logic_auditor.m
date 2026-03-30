% ==============================================================================
% MATLAB LOGIC AUDITOR & ADAPTIVE DEBUGGER
% Giam vung hoi tu cham, Nhan dien sai so tich luy (Precision Loss)
% Va kiem tra tinh hieu qua cua phuong trinh vi phan hay Newton-Raphson
% ==============================================================================

function [x_opt, iters, status] = matlab_logic_auditor(func, dfunc, x0, tol, max_iters)
    fprintf('\\n======================================================\\n');
    fprintf('           MATLAB LOGIC AUDITOR (THE HUMAN LENS)        \\n');
    fprintf('======================================================\\n');
    fprintf('Dang phan tich ham so va dao ham. Gia lap vung hoi tu...\\n\\n');

    x = x0;
    iters = 0;
    status = 'Convergent';

    % Danh gia diem khoi dau (Derivate is nearing 0 ?)
    if abs(dfunc(x0)) < 1e-10
        fprintf('[WARNING] Diem khoi dau (Initial Point) dao ham qua nho.\\n');
        fprintf('-> Newton-Raphson se phan ky. Hay chon x0 gan nghiem hon.\\n');
        status = 'Divergent: Derivative ~ 0';
        return;
    end

    while iters < max_iters
        f_val = func(x);
        df_val = dfunc(x);

        if abs(f_val) < tol
            fprintf('[SUCCESS] Da hoi tu thanh cong tai x = %.7f sau %d buoc.\\n', x, iters);
            status = 'Convergent';
            break;
        end

        % Kiem tra Inf hoac NaN
        if isinf(f_val) || isnan(f_val)
            fprintf('[ERROR] Vung khong hop le sinh ra NaN/Inf.\\n');
            fprintf('-> Phuong trinh co the co asympote chua duoc xy ly.\\n');
            status = 'Divergent: Overflow';
            break;
        end

        % Update buoc nhay
        step_size = f_val / df_val;
        
        % Cham sat do chinh xac (Precision Loss tracking)
        if abs(step_size) > 1e10
            fprintf('[WARNING] Buoc nhay qua lon. Tu dong chuyen sang Adaptive Step.\\n');
            step_size = sign(step_size) * 1e3; % Limit step
        end

        x = x - step_size;
        iters = iters + 1;
    end

    if iters == max_iters && abs(f_val) >= tol
        fprintf('[WARNING] Qua trinh dao dong khong hoi tu, Max Iters reched = %d.\\n', max_iters);
        fprintf('-> Nghiem dang di qua lai tai mot diem Min/Max hoac khong co the chia (Zero Division).\\n');
        status = 'Oscillating (Max Iters)';
    end

    x_opt = x;
    fprintf('\\n[THE ADVISTOR:] Kiem toan Logic hoan tat. Chuc ban hoc thuat toi da!\\n');
    fprintf('======================================================\\n');
end

% Function Tests
% f = @(x) x^3 - 2*x - 5;
% df = @(x) 3*x^2 - 2;
% [root, iters, stat] = matlab_logic_auditor(f, df, 2, 1e-6, 100);
