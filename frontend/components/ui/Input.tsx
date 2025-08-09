'use client';
import React, { forwardRef } from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';

/**
 * Input compatível com framer-motion v11:
 * - Usa APENAS HTMLMotionProps<'input'> (não mistura com InputHTMLAttributes).
 * - Omite handlers de animação que conflitam (onAnimationStart/End/Iteration/Complete).
 * - Mantém whileFocus/transition configuráveis.
 */
type MotionSafeInputProps = Omit<
  HTMLMotionProps<'input'>,
  'children' | 'onAnimationStart' | 'onAnimationEnd' | 'onAnimationIteration' | 'onAnimationComplete'
>;

interface InputProps extends MotionSafeInputProps {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      icon,
      iconPosition = 'left',
      fullWidth = false,
      className = '',
      whileFocus = { scale: 1.01 },
      transition = { duration: 0.2 },
      ...props
    },
    ref
  ) => {
    const inputClasses = [
      'input',
      error ? 'input-error' : '',
      icon ? (iconPosition === 'left' ? 'pl-10' : 'pr-10') : '',
      fullWidth ? 'w-full' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className={fullWidth ? 'w-full' : ''}>
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div
              className={`absolute inset-y-0 ${
                iconPosition === 'left' ? 'left-0 pl-3' : 'right-0 pr-3'
              } flex items-center pointer-events-none`}
            >
              <span className={`text-gray-400 ${error ? 'text-red-400' : ''}`}>
                {icon}
              </span>
            </div>
          )}

          <motion.input
            ref={ref}
            className={inputClasses}
            whileFocus={whileFocus}
            transition={transition}
            {...props}
          />
        </div>

        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        {helperText && !error && (
          <p className="mt-1 text-sm text-gray-500">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
